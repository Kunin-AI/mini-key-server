# -*- coding: utf-8 -*-
"""Model unit tests."""
import datetime as dt

import pytest

from keyserv.models import Application, Key, Event, AuditLog

from tests import freeze_time, fake

@pytest.mark.usefixtures('db')
class TestApplication:
    """User tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User('foo', 'foo@bar.com')
        user.save()

        retrieved = User.get_by_id(user.id)
        assert retrieved == user
        retrieved = User.get_by_uuid(user.uuid)
        assert retrieved == user

    def test_created_at_defaults_to_datetime(self):
        """Test creation date."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert bool(user.created_at)
        assert isinstance(user.created_at, dt.datetime)

    def test_password_is_nullable(self):
        """Test null password."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert user.password is None

    def test_registered_unverified(self):
        """Test start unverified."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert user.confirmed is False

    def test_registered_no_confirmedon(self):
        """Test start unconfirmed date."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert user.confirmed_on is None

    def test_registered_notadmin(self):
        """Test start not admin."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert user.admin is False

    def test_registered_admin_is_admin(self):
        """Test admin creation."""
        user = User(username='foo', email='foo@bar.com', admin=True)
        user.save()
        assert user.admin is True

    def test_registered_confirmed_is_confirmed(self):
        """Test confirmed creation."""
        user = User(username='foo', email='foo@bar.com', confirmed=True, confirmed_on=dt.datetime.today())
        user.save()
        assert user.confirmed is True

    def test_registered_confirmedon_wields_confirmed(self):
        """Test confirmedon == confirmed."""
        user = User(username='foo', email='foo@bar.com', confirmed_on=dt.datetime.today())
        user.save()
        assert user.confirmed is True

    @freeze_time('2019-12-31')
    def test_registered_confirmedon_date(self):
        """Test confirmed date."""
        user = User(username='foo', email='foo@bar.com', confirmed_on=dt.datetime.today())
        user.save()
        assert user.confirmed_on == dt.datetime(2019,12,31)

    @freeze_time('2019-12-31')
    def test_registered_confirmedon_date_without_passing_date(self):
        """Test confirmed date is now."""
        user = User(username='foo', email='foo@bar.com', confirmed=True)
        user.save()
        assert user.confirmed_on == dt.datetime(2019,12,31)

    @freeze_time('2019-12-31')
    def test_confirm_after_create(self):
        """Test confirm after user creation"""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        user.confirm() # i.e. confirm NOW
        assert bool(user.confirmed)
        assert user.confirmed_on == dt.datetime(2019,12,31)
        assert user.updated_at == dt.datetime(2019,12,31)

    @freeze_time('2019-12-31')
    def test_confirm_after_create_with_date(self):
        """Test confirm after user creation passing in a date of confirmation"""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        user.confirm(dt.datetime(2019,10,8))
        assert bool(user.confirmed)
        assert user.confirmed_on != dt.datetime(2019,12,31)
        assert user.confirmed_on == dt.datetime(2019,10,8)
        assert user.updated_at == dt.datetime(2019,12,31)

    @freeze_time('2019-12-31')
    def test_promote_to_admin(self):
        """Test promoting to admin after user created"""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        user.promote()
        assert bool(user.admin)
        assert user.updated_at == dt.datetime(2019,12,31)

    @freeze_time('2019-12-31')
    def test_demote_from_admin(self):
        """Test demoting from admin"""
        user = User(username='foo', email='foo@bar.com', admin=True)
        user.save()
        user.demote()
        assert not bool(user.admin)
        assert user.updated_at == dt.datetime(2019,12,31)

    def test_make_admin(self):
        """Test promoting to admin after user created"""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        user.make_admin()
        assert bool(user.admin)

    def test_factory(self, db):
        """Test user factory."""
        from tests.factories import ClientFactory
        c = ClientFactory()
        user = UserFactory.create(client=c, password='myprecious')
        db.session.commit()
        assert bool(user.username)
        assert bool(user.email)
        assert bool(user.first_name)
        assert bool(user.last_name)
        assert bool(user.created_at)
        assert bool(user.client)
        assert user.check_password('myprecious')

    def test_check_password(self):
        """Check password."""
        user = User.create(username='foo', email='foo@bar.com',
                           password='foobarbaz123')
        assert user.check_password('foobarbaz123')
        assert not user.check_password('barfoobaz')

    def test_set_password_after_user_creation(self):
        """Check set_password."""
        user = User.create(username='foo', email='foo@bar.com')
        assert not bool(user.password)
        user.set_password('321zabraboof')
        assert user.check_password('321zabraboof')

    def test_has_client(self):
        """Check that a user has a client and client_id."""
        from kunin.taxonomy.client.models import Client
        user = User('foo', 'foo@bar.com')
        client = Client(fake.company())
        user.client = client
        user.save()

        assert user.client == client
        assert user.client_id == client.id

