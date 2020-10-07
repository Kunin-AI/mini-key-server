# coding: utf-8

from flask import url_for
from kunin.exceptions import USER_ALREADY_REGISTERED
from tests import fake


def _register_user(testapp, **kwargs):
    return testapp.post_json(url_for("user.register_user"), {
        "user": {
            "username": "mo",
            "email": "mo@mo.mo",
            "password": "momo",
            "bio": fake.sentence(),
            "first_name": "Mo",
            "last_name": "Om",
            "image": fake.url()
        }
    }, **kwargs)


class TestAuthenticate:

    def test_register_user(self, testapp):
        resp = _register_user(testapp)
        assert resp.status_code == 201
        assert resp.json['user']['email'] == 'mo@mo.mo'
        assert resp.json['user']['first_name'] == 'Mo'
        assert resp.json['user']['last_name'] == 'Om'
        assert bool(resp.json['user']['bio'])
        assert bool(resp.json['user']['image'])
        assert not bool(resp.json['user']['confirmed'])
        assert not bool(resp.json['user']['admin'])
        assert resp.json['user']['access_token'] != None
        assert resp.json['user']['refresh_token'] == None
        assert len(resp.json['user']['access_token']) > 36

    def test_user_login(self, testapp):
        _register_user(testapp)

        resp = testapp.post_json(url_for('user.login_user'), {
            'user': {
                'email': 'mo@mo.mo',
                'password': 'momo'
            }
        })

        assert resp.status_code == 200
        assert resp.json['user']['email'] == 'mo@mo.mo'
        resp = testapp.post_json(url_for('user.login_user'), {
            'user': {
                'username': 'mo@mo.mo',
                'password': 'momo'
            }
        })
        assert resp.status_code == 200
        assert resp.json['user']['first_name'] == 'Mo'
        assert resp.json['user']['last_name'] == 'Om'
        assert bool(resp.json['user']['bio'])
        assert bool(resp.json['user']['image'])
        assert not bool(resp.json['user']['confirmed'])
        assert not bool(resp.json['user']['admin'])
        assert resp.json['user']['access_token'] != None
        assert resp.json['user']['refresh_token'] == None
        assert len(resp.json['user']['access_token']) > 36

    def test_get_user(self, testapp):
        resp = _register_user(testapp)
        token = str(resp.json['user']['access_token'])
        resp = testapp.get(url_for('user.get_user'), headers={
            'Authorization': 'Token {}'.format(token)
        })
        assert resp.status_code == 200
        assert resp.json['user']['email'] == 'mo@mo.mo'
        assert resp.json['user']['access_token'] == token
        assert resp.json['user']['token_type'] == 'jwt'
        assert not bool(resp.json['user']['refresh_token'])

    def test_register_already_registered_user(self, testapp):
        _register_user(testapp)
        resp = _register_user(testapp, expect_errors=True)
        assert resp.status_code == 422
        assert resp.json == USER_ALREADY_REGISTERED['message']

    def test_update_user(self, testapp):
        from dateutil.parser import parse
        resp = _register_user(testapp)
        token = str(resp.json['user']['access_token'])
        resp = testapp.put_json(url_for('user.update_user'), {
            'user': {
                'email': 'meh@mo.mo',
                'bio': 'I\'m a simple man',
                'password': 'hmm'
            }
        }, headers={
            'Authorization': 'Token {}'.format(token)
        })
        assert resp.status_code == 200
        assert resp.json['user']['bio'] == 'I\'m a simple man'
        assert resp.json['user']['email'] == 'meh@mo.mo'
        assert parse(resp.json['user']['created_at']) < parse(resp.json['user']['updated_at'])
        assert parse(resp.json['user']['created_at']).timestamp() - \
               parse(resp.json['user']['updated_at']).timestamp() < 0.1
