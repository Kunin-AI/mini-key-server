# MIT License

# Copyright (c) 2019 Samuel Hoffman

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from flask import request
from flask_restful import Api, Resource, reqparse

from keyserv.keymanager import (Origin, activate_key_unsafe, key_exists_const,
                                key_get_unsafe, key_valid_const, key_still_valid, key_for_kunin_client_employee)
from keyserv.models import Application

api = Api()


class ActivateKey(Resource):
    """Endpoint used for key activation."""

    def post(self):
        """
        Activate a key

        Activates a live key; will either allow key activation or deny if there
        are no more key activations left. Function will log attempts to
        activate regardless of success or failure.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("token", required=True)
        parser.add_argument("machine", required=True)
        parser.add_argument("user", required=True)
        parser.add_argument("app_id", required=True, type=int)
        parser.add_argument("hwid", required=True)
        # parser.add_argument("valid_until", required=True)
        parser.add_argument("email")
        parser.add_argument("password")
        args = parser.parse_args()

        origin = Origin(request.remote_addr, args.machine,
                        args.user, args.hwid)

        if not key_exists_const(args.app_id, args.token, origin):
            resp = {"result": "failure", "error": "invalid activation token", "support_message": None}
            if args.app_id:
                app = Application.query.get(args.app_id)
                if app and app.support_message:
                    resp["support_message"] = app.support_message
            return resp, 404

        key = key_get_unsafe(args.app_id, args.token, origin)

        if key.remaining == 0:
            resp = {"result": "failure", "error": "key is out of activations",
                    "support_message": key.app.support_message}
            return resp, 410

        if not key_still_valid(key):
            resp = {"result": "failure", "error": "key is no longer valid",
                    "support_message": key.app.support_message}
            return resp, 410

        # setup the new account using the key's kunin_client_id, kunin_email and kunin_password
        kunin_employee_id = key_for_kunin_client_employee(key, key.kunin_client_id, args.email, args.password, origin)
        if not kunin_employee_id:
            resp = {"result": "failure", "error": "this account is already registered (or has had a trial)",
                    "support_message": key.app.support_message}
            return resp, 410

        activation = activate_key_unsafe(args.app_id, args.token, kunin_employee_id, origin)

        return {"result": "ok",
                "remainingActivations": str(key.remaining),
                "expiresOn": str(activation.valid_until),
                "kunin_employee_id": kunin_employee_id,
                "kunin_client_id": key.kunin_client_id}, 201


class CheckKey(Resource):
    """Endpoint used for checking if a key is valid."""

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("token", required=True, location='args')
        parser.add_argument("machine", required=True, location='args')
        parser.add_argument("user", required=True, location='args')
        parser.add_argument("hwid", required=True, location='args')
        parser.add_argument("app_id", required=True, type=int, location='args')
        # parser.add_argument("kunin_employee_id", required=True, type=int, location='args')
        # parser.add_argument("kunin_client_id", required=True, type=int, location='args')

        args = parser.parse_args()

        origin = Origin(request.remote_addr, args.machine, args.user, args.hwid)

        possibly_valid_key = key_valid_const(args.app_id, args.token, origin)
        activation = None
        # activation = [a for a in possibly_valid_key.activations if a.kunin_employee_id == args.kunin_employee_id]
        # activation = activation[0] if activation else None
        if possibly_valid_key and key_still_valid(possibly_valid_key, activation):
            from hmac import compare_digest
            if not compare_digest(origin.hwid, possibly_valid_key.hwid):
                return {"result": "ok"}, 201
            else:
                return {"result": "ok"}, 200

        if not possibly_valid_key:
            return {"result": "failure", "error": "invalid key"}, 404
        else:
            expiry = activation.valid_until if activation else possibly_valid_key.valid_until
            return {"result": "failure", "error": "invalid key; expired f{expiry}"}, 404


api.add_resource(ActivateKey, "/api/activate")
api.add_resource(CheckKey, "/api/check")
