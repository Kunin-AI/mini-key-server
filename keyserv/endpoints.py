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


import hmac
from datetime import datetime

from flask import request, current_app
from flask_restful import Api, Resource, reqparse

from keyserv.keymanager import (Origin, activate_key_unsafe, key_exists_const,
                                key_get_unsafe, key_valid_const, key_still_valid, key_for_kunin_client_employee)
from keyserv.models import Application, EarlyBirdApplication, Key, db

api = Api()


def _cors_headers():
    return {
        "Access-Control-Allow-Origin": "https://firstbell.1000ml.io",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


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
        parser.add_argument("email")
        parser.add_argument("password")
        args = parser.parse_args()

        origin = Origin(request.remote_addr, args.machine, args.user, args.hwid)

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
        kunin_employee_id = 0
        if key.kunin_client_id:
            kunin_employee_id = key_for_kunin_client_employee(key, key.kunin_client_id, args.email, args.password, origin)
            if not kunin_employee_id:
                resp = {"result": "failure", "error": "this account is already registered (or has had a trial)",
                        "support_message": key.app.support_message}
                return resp, 410

        activation = activate_key_unsafe(args.app_id, args.token, kunin_employee_id, origin, key)

        return {"result": "ok",
                "remainingActivations": str(key.remaining) if key.remaining != -1 else 'unlimited',
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
        parser.add_argument("kunin_employee_id", required=False, type=int, location='args')
        parser.add_argument("kunin_client_id", required=False, type=int, location='args')

        args = parser.parse_args()

        origin = Origin(request.remote_addr, args.machine, args.user, args.hwid)

        possibly_valid_key = key_valid_const(args.app_id, args.token, origin)
        activation = None
        if args.kunin_employee_id and possibly_valid_key:
            activation = [a for a in possibly_valid_key.activations if a.kunin_employee_id == args.kunin_employee_id
                          and a.hwid == args.hwid]
            activation = activation[0] if activation else None
        if possibly_valid_key and key_still_valid(possibly_valid_key, activation):
            expiry = {"expiresOn": str(activation.valid_until)} if activation else {}
            remaining = str(possibly_valid_key.remaining) if possibly_valid_key.remaining != -1 else 'unlimited'
            return {**{"remainingActivations": remaining, "kunin_employee_id": args.kunin_employee_id,
                       "result": "ok", "kunin_client_id": possibly_valid_key.kunin_client_id}, **expiry}, \
                200 if activation else 201

        if not possibly_valid_key:
            return {"result": "failure", "error": "invalid key"}, 404
        else:
            expiry = activation.valid_until if activation else possibly_valid_key.valid_until
            return {"result": "failure", "error": f"invalid key; expired {expiry}"}, 404


class GetAppId(Resource):
    """Endpoint used for checking if a key is valid."""

    def get(self):
        """
        Check if a key is valid
        """
        parser = reqparse.RequestParser()
        parser.add_argument("token", required=True, location='args')

        args = parser.parse_args()

        key = Key.query.filter_by(token=args.token).first()
        if key:
            return {"result": "ok", "app_id": key.app_id}, 200
        else:
            return {"result": "failure", "error": "invalid key"}, 404


class ClaimKey(Resource):
    """Allocate an unclaimed key from the pool for a given email."""

    def post(self):
        api_key = request.headers.get("X-Api-Key", "")
        expected = current_app.config.get("CLAIM_API_KEY", "")
        if not expected or not hmac.compare_digest(api_key, expected):
            return {"result": "failure", "error": "unauthorized"}, 401

        parser = reqparse.RequestParser()
        parser.add_argument("email", required=True)
        parser.add_argument("app_id", required=True, type=int)
        parser.add_argument("name", required=False)
        args = parser.parse_args()

        # check if this email already claimed a key for this app
        existing = Key.query.filter_by(app_id=args.app_id, claimed_by=args.email).first()
        if existing:
            token = existing.token
            formatted = '-'.join([token[i:i+5] for i in range(0, len(token), 5)])
            return {"result": "ok", "token": formatted, "already_claimed": True}, 200

        # find an unclaimed key with remaining activations
        key = Key.query.filter_by(app_id=args.app_id, claimed_by=None, enabled=True) \
            .filter(Key.remaining != 0).first()

        if not key:
            return {"result": "failure", "error": "no keys available"}, 410

        key.claimed_by = args.email
        key.claimed_at = datetime.utcnow()
        if args.name:
            key.memo = f"early-tester: {args.name} <{args.email}>"
        else:
            key.memo = f"early-tester: {args.email}"
        db.session.commit()

        token = key.token
        formatted = '-'.join([token[i:i+5] for i in range(0, len(token), 5)])
        return {"result": "ok", "token": formatted, "already_claimed": False}, 201


class ApplyEarlyBird(Resource):
    """Public endpoint for First Bell early access applications."""

    def options(self):
        return "", 204, _cors_headers()

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", required=True)
        parser.add_argument("email", required=True)
        parser.add_argument("school", required=True)
        parser.add_argument("subjects", required=True)
        parser.add_argument("grade_levels", required=True)
        parser.add_argument("class_size", required=True)
        parser.add_argument("uses_handwritten_tests", required=True)
        parser.add_argument("motivation", required=True)
        parser.add_argument("how_heard")
        args = parser.parse_args()

        existing = EarlyBirdApplication.query.filter_by(email=args.email).first()
        if existing:
            return {"result": "ok", "message": "already applied"}, 200, _cors_headers()

        app = EarlyBirdApplication(
            name=args.name,
            email=args.email,
            school=args.school,
            subjects=args.subjects,
            grade_levels=args.grade_levels,
            class_size=args.class_size,
            uses_handwritten_tests=args.uses_handwritten_tests,
            motivation=args.motivation,
            how_heard=args.how_heard or "",
        )
        db.session.add(app)
        db.session.commit()

        return {"result": "ok", "message": "application received"}, 201, _cors_headers()


class EarlyBirdSpots(Resource):
    """Public endpoint returning how many First Bell spots remain."""

    def options(self):
        return "", 204, _cors_headers()

    def get(self):
        claimed = EarlyBirdApplication.query.filter_by(status=1).count()
        return {"total": 20, "claimed": claimed}, 200, _cors_headers()


api.add_resource(ActivateKey, "/api/activate")
api.add_resource(CheckKey, "/api/check")
api.add_resource(GetAppId, "/api/appid")
api.add_resource(ClaimKey, "/api/claim")
api.add_resource(ApplyEarlyBird, "/api/apply")
api.add_resource(EarlyBirdSpots, "/api/spots")