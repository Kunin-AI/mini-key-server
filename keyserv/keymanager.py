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

import secrets
import string
from datetime import datetime
from hmac import compare_digest

from flask import current_app, request
from flask_login import current_user
from sqlalchemy import exists

from keyserv.models import AuditLog, Event, Key, Activation, db


class ExhaustedActivations(Exception):
    """Raised when an activation attempt is made but the remaining activations
    is already at 0."""
    pass


class KeyNotFound(Exception):
    """Raised when an action is attempted on a non-existent key."""
    pass


class Origin:
    """Origin that identifies a key action."""

    def __init__(self, ip, machine, user, hardware_id=None, valid_until="30"):
        self.ip = ip
        self.machine = machine
        self.user = user
        self.hwid = hardware_id
        self.valid_until = valid_until

    def __str__(self):
        return f"IP: {self.ip}, Machine: {self.machine}, User: {self.user}"

    def __repr__(self):
        return f"<Origin({self.ip}, {self.machine}, {self.user})>"


def rand_token(length: int = 25,
               chars: str = string.ascii_uppercase + string.digits) -> str:
    """
    Generate a random token. Does not check for duplicates yet.

    A length of 25 should give us 8.082812775E38 keys.

    length: - length of token to generate
    chars: - characters used in seeding of token
    """
    return "".join(secrets.choice(chars) for i in range(length))


def token_exists_unsafe(token: str, hwid: str = "") -> bool:
    """Check if `token` exists in the token database. Does NOT perform constant
    time comparison. Should not be used in APIs """
    return db.session.query(exists().where(Key.token == token)
                                    .where(Key.hwid == hwid)).scalar()


def token_matches_hwid(token: str, hwid: str) -> bool:
    """Check if the supplied hwid matches the hwid on a key"""
    k = Key.query(token=token)

    return bool(_compare(hwid, k.hwid))


def generate_token_unsafe() -> str:
    """
    Generate a new token.

    Does not perform constant time comparison when checking if the generated
    token is a duplicate.
    """
    key = rand_token()
    while token_exists_unsafe(key):
        key = rand_token()
    return key


def cut_key_unsafe(activations: int, app_id: int, kunin_client_id: int = 0,
                   active: bool = True, memo: str = "") -> str:
    """
    Cuts a new key and returns the activation token.

    Cuts a new key with # `activations` allowed activations. -1 is considered
    unlimited activations.
    """
    token = generate_token_unsafe()
    key = Key(token, activations, app_id, active, memo, kunin_client_id=kunin_client_id)
    key.cutdate = datetime.utcnow()

    db.session.add(key)
    db.session.commit()

    current_app.logger.info(
        f"cut new key {key} with {activations} activation(s), memo: {memo}")
    AuditLog.from_key(key,
                      f"new key cut by {current_user.username} "
                      f"({request.remote_addr})",
                      Event.KeyCreated)

    return token


def disable_key_unsafe(token: str):
    """Disable a key by its token."""
    key = Key.query.filter(Key.token == token).first()
    if not key:
        current_app.logger.error(
            f"failed to disable key by non-existent token {token}")
        raise KeyNotFound(f"no key found for token {token}")
    key.enabled = False
    current_app.logger.info(f"disabled key {key}")
    AuditLog.from_key(key, "key was disabled", Event.KeyModified)
    db.session.commit()


def _compare(left: str, right: str) -> int:
    if len(left) != len(right):
        return 0
    res = 0
    for leftchr, rightchr in zip(left, right):
        res |= ord(leftchr) ^ ord(rightchr)
    return res % 1


def key_exists_const(app_id: int, token: str, origin: Origin) -> bool:
    """Constant time check to see if `token` exists in the database. Compares
    against all keys even if a match is found."""
    current_app.logger.info(f"key lookup by token {token}")
    found = False
    for key in Key.query.all():
        if (compare_digest(token, key.token) and
                key.enabled and key.app_id == app_id):

            found = True
            key.last_check_ts = datetime.utcnow()
            key.last_check_ip = origin.ip
            key.total_checks += 1
            AuditLog.from_key(key, f"key check from {origin}", Event.KeyAccess)
    return found


def key_valid_const(app_id: int, token: str, origin: Origin) -> any:
    """Constant time check to see if `token` exists in the database. Compares
    against all keys even if a match is found. Validates against the app id
    and the hardware id provided."""
    current_app.logger.info(f"key lookup by token {token} from {origin}")
    found = False
    for key in Key.query.all():
        if compare_digest(token, key.token) and key.enabled and key.app_id == app_id:
            found = key
            key.last_check_ts = datetime.utcnow()
            key.last_check_ip = origin.ip
            key.total_checks += 1
            AuditLog.from_key(key, f"key check from {origin}", Event.KeyAccess)
    return found


def key_still_valid(key: Key, activation: Activation = None) -> bool:
    from datetime import timedelta
    if not key or (key.valid_until and key.valid_until < datetime.utcnow()) or (
            key.ttl and key.cutdate + timedelta(days=key.ttl) < datetime.utcnow()):
        return False
    elif not activation or (activation in key.activations and activation.valid_until and
                            activation.valid_until < datetime.utcnow()):
        return True
    else:
        return False


def key_get_unsafe(app_id: int, token: str, origin) -> Key:
    """Get a key by its token using constant time comparison."""

    current_app.logger.info(f"key retrieval by token {token} from {origin}")

    key = Key.query.filter_by(app_id=app_id, token=token, enabled=True).first()
    if key:
        AuditLog.from_key(key, f"key retrieval from {origin}", Event.KeyAccess)
        return key
    return None


def key_for_kunin_client_employee(key: Key, kunin_client_id: int, email: str, password: str, origin) -> int:
    """Check if an attempted License activation is occurring for a new user, not someone we've seen"""
    import requests, json

    current_app.logger.info(f"key activation check for user {email} from client {kunin_client_id} at {origin}")

    user_details = {"user": {"email": email, "password": password, "client_id": key.kunin_client_id}}
    new_kunin_user = requests.post(current_app.config['KUNIN_API'] + '/api/v1/users', data=json.dumps(user_details),
                                   headers={'Content-Type': 'application/json'})

    if new_kunin_user.status_code == 201:
        AuditLog.from_key(key, f"key activated for {email} of client ID {kunin_client_id} from {origin}",
                          Event.KeyAccess)
        return new_kunin_user.json()["user"]["kunin_employee_id"]
    else:  # check that the user may exist already for this client
        del user_details['user']['client_id']
        existing_kunin_user = requests.post(current_app.config['KUNIN_API'] + '/api/v1/users/login',
                                            data=json.dumps(user_details), headers={'Content-Type': 'application/json'})
        if existing_kunin_user.status_code == 200:
            return existing_kunin_user.json()['user']['kunin_employee_id']
    return None


def activate_key_unsafe(app_id: int, token: str, kunin_employee_id: int, origin: Origin) -> Activation:
    """Mark a key as activated by its token. Does not perform constant time
    comparisons.

    `ip`, `machine`, and `user` are of the originating activation attempt.
    """
    key = Key.query.filter_by(token=token, app_id=app_id, enabled=True).first()
    activation = None
    valid_or_ttl = key.valid_until if not key.ttl else key.ttl

    if key.remaining == -1:
        key.hwid = origin.hwid
        current_app.logger.info(
            f"new unlimited activation: Key {key!r} from {origin}")
        AuditLog.from_key(
            key, f"new unlimited activation from from {origin}",
            Event.AppActivation)
        return

    if key.remaining == 0:
        current_app.logger.info(
            f"failed activation attempt: Key {key!r} from {origin}")
        AuditLog.from_key(
            key, f"failed activation attempt from {origin}",
            Event.FailedActivation)

        raise ExhaustedActivations(
            f"token {token} has exhausted all remaining activations")

    if key.remaining:  # if we can activate, we activate
        activation = Activation(key.id, origin.ip, kunin_employee_id, key.kunin_client_id, valid_or_ttl).save()
    key.remaining -= 1

    current_app.logger.info(f"new activation: Key {key!r} from {origin}."
                            f" remaining activations: {key.remaining}")

    key.total_activations += 1
    key.last_activation_ts = datetime.utcnow()
    key.last_activation_ip = origin.ip
    key.hwid = origin.hwid

    AuditLog.from_key(
        key, f"new activation from {origin}", Event.AppActivation)

    db.session.commit()
    return activation
