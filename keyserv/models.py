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

from datetime import datetime, timedelta
from enum import IntEnum
from typing import Any  # NOQA: F401
from flask_caching import Cache

from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy, Model
from keyserv.uuidgenerator import UUIDGenerator

basestring = (str, bytes)
cache = Cache()


class CRUDMixin(Model):
    """Mixin that adds convenience methods for CRUD (create, read, update, delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()


db = SQLAlchemy(model_class=CRUDMixin)


# From Mike Bayer's "Building the app" talk
# https://speakerdeck.com/zzzeek/building-the-app
class SurrogatePK(object):
    """A mixin that adds a surrogate integer 'primary key' column named ``id`` \
        to any declarative-mapped class.
    """

    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.CHAR(36), index=True)

    @classmethod
    def get_by_id(cls, record_id):
        """Get record by ID."""
        if any(
                (isinstance(record_id, basestring) and record_id.isdigit(),
                 isinstance(record_id, (int, float))),
        ):
            return cls.query.get(int(record_id))

    @classmethod
    def get_by_uuid(cls, record_uuid):
        """Get record by UUID."""
        from keyserv.uuidgenerator import UUIDGenerator
        return cls.query.get(int(UUIDGenerator.uuid_to_int(str(record_uuid))))


def reference_col(tablename, nullable=False, pk_name='id', **kwargs):
    """Column that adds primary key foreign key reference.

    Usage: ::

        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(tablename, pk_name)),
        nullable=nullable, **kwargs)


class Application(db.Model, SurrogatePK):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    support_message = db.Column(db.String(255))

    def __init__(self, name=None, support_message=None):
        self.name = name
        self.support_message = support_message


@event.listens_for(Application, 'after_insert')
def after_insert(_, connection, target):
    if not target.uuid:  # Generate UUID
        myuuid = UUIDGenerator.int_to_uuid(target.id).hex
        connection.execute(Application.__table__.update().where(Application.id == target.id).values(uuid=myuuid))


class Key(db.Model, SurrogatePK):
    """
    Database representation of a software key provided by MKS.

    Id: identifier for a kkey
    token: the license token fed to the program
    remaining: remaining activations for a key. -1 if unlimited
    enabled: if the license is able to
    """
    id = db.Column(db.Integer, primary_key=True)
    app = db.relationship("Application", uselist=False, backref="keys")
    app_id = db.Column(db.Integer,
                       db.ForeignKey("application.id"), nullable=False)
    cutdate = db.Column(db.DateTime(timezone=True))
    enabled = db.Column(db.Boolean, default=True)
    memo = db.Column(db.String(512))
    kunin_client_id = db.Column(db.Integer)
    # hwid = db.Column(db.String, default="")
    remaining = db.Column(db.Integer)
    token = db.Column(db.String(512), unique=True)
    total_activations = db.Column(db.Integer, default=0)
    total_checks = db.Column(db.Integer, default=0)
    last_activation_ts = db.Column(db.DateTime)
    last_activation_ip = db.Column(db.String(64))
    last_check_ts = db.Column(db.DateTime)
    last_check_ip = db.Column(db.String(64))
    valid_until = db.Column(db.DateTime(timezone=True))
    ttl = db.Column(db.Integer)
    claimed_by = db.Column(db.String(255))
    claimed_at = db.Column(db.DateTime)

    def __init__(self, token: str, remaining: int, app_id: int, enabled: bool = True, memo: str = "", # hwid: str = "",
                 expiry_date: str = "30", kunin_client_id: int = 0) -> None:
        self.token = token
        self.remaining = remaining
        self.enabled = enabled
        self.memo = memo
        self.app_id = app_id
        # self.hwid = hwid
        if expiry_date.isnumeric():
            self.valid_until = datetime.utcnow() + timedelta(days=int(expiry_date))
            self.ttl = int(expiry_date)
        else:
            from dateutil.parser import parse
            self.valid_until = parse(expiry_date)
            self.ttl = (datetime.utcnow() - self.valid_until).days
        if kunin_client_id:
            self.kunin_client_id = kunin_client_id

    def __str__(self):
        return f"<Key({self.token}) valid until {self.valid_until}>"


@event.listens_for(Key, 'after_insert')
def after_insert(_, connection, target):
    if not target.uuid:  # Generate UUID
        myuuid = UUIDGenerator.int_to_uuid(target.id).hex
        connection.execute(Key.__table__.update().where(Key.id == target.id).values(uuid=myuuid))


class Activation(db.Model, SurrogatePK):
    """
    Database representation of the activation of a software key provided by MKS.

    id: identifier for a activation
    key: the key associated with this activation
    valid_until: taking into account how the key was cut, the date when this is NO LONGER valid
    """
    id = db.Column(db.Integer, primary_key=True)
    key = db.relationship("Key", uselist=False, backref="activations")
    key_id = db.Column(db.Integer,
                       db.ForeignKey("key.id"), nullable=False)
    hwid = db.Column(db.String(128), default="")
    activation_ts = db.Column(db.DateTime(timezone=True))
    activation_ip = db.Column(db.String(64))
    kunin_employee_id = db.Column(db.Integer)
    kunin_client_id = db.Column(db.Integer)
    valid_until = db.Column(db.DateTime(timezone=True))

    def __init__(self, key_id: int, ip: str = "", kunin_client_id: int = 0, kunin_employee_id: int = 0, 
                 expiry_date: str = "30", hwid: str = "") -> None:
        self.key_id = key_id
        self.activation_ip = ip
        self.kunin_client_id = kunin_client_id
        self.kunin_employee_id = kunin_employee_id
        self.hwid = hwid
        if isinstance(expiry_date, int) or expiry_date.isnumeric():
            self.valid_until = datetime.utcnow() + timedelta(days=int(expiry_date))
        else:
            from dateutil.parser import parse
            self.valid_until = parse(expiry_date)
        self.activation_ts = datetime.utcnow()

    def __str__(self):
        return f"<Activation [of Key({self.token})] valid until {self.valid_until}>"


@event.listens_for(Activation, 'after_insert')
def after_insert(_, connection, target):
    if not target.uuid:  # Generate UUID
        myuuid = UUIDGenerator.int_to_uuid(target.id).hex
        connection.execute(Activation.__table__.update().where(Activation.id == target.id).values(uuid=myuuid))


class Event(IntEnum):
    Info = 0
    Warn = 1
    Error = 2
    AppActivation = 3
    FailedActivation = 4
    KeyModified = 5
    KeyCreated = 6
    KeyAccess = 7
    AppCreated = 8
    AppModified = 9


class AuditLog(db.Model, SurrogatePK):
    """
    Database representation of an audit log.
    """
    id = db.Column(db.Integer, primary_key=True)
    app = db.relationship("Application", backref="logs")
    app_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    event_type = db.Column(db.Integer)
    key = db.relationship("Key", uselist=False, backref="logs")
    key_id = db.Column(db.Integer, db.ForeignKey("key.id"), nullable=False)
    message = db.Column(db.String(512))
    timestamp = db.Column(db.DateTime)

    def __init__(self, key_id: int, app_id: int,
                 message: str, event_type: Event) -> None:
        self.key_id = key_id
        self.app_id = app_id
        self.message = message
        self.event_type = int(event_type)
        self.timestamp = datetime.now()

    @classmethod
    def from_key(cls, key: Key, message: str, event_type: Event):
        cls(key.id, key.app.id, message, event_type).save()


@event.listens_for(AuditLog, 'after_insert')
def after_insert(_, connection, target):
    if not target.uuid:  # Generate UUID
        myuuid = UUIDGenerator.int_to_uuid(target.id).hex
        connection.execute(AuditLog.__table__.update().where(AuditLog.id == target.id).values(uuid=myuuid))


class EarlyBirdApplication(db.Model, SurrogatePK):
    __tablename__ = 'early_bird_application'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    school = db.Column(db.String(255))
    subjects = db.Column(db.String(512))
    grade_levels = db.Column(db.String(255))
    class_size = db.Column(db.String(64))
    uses_handwritten_tests = db.Column(db.String(32))
    how_heard = db.Column(db.String(512))
    motivation = db.Column(db.Text)
    status = db.Column(db.Integer, default=0)  # 0=pending, 1=approved, 2=rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewer_notes = db.Column(db.Text, nullable=True)
    key_id = db.Column(db.Integer, db.ForeignKey('key.id'), nullable=True)
    key = db.relationship('Key', uselist=False, backref='early_bird_application')


@event.listens_for(EarlyBirdApplication, 'after_insert')
def after_insert(_, connection, target):
    if not target.uuid:
        myuuid = UUIDGenerator.int_to_uuid(target.id).hex
        connection.execute(
            EarlyBirdApplication.__table__.update()
            .where(EarlyBirdApplication.id == target.id)
            .values(uuid=myuuid)
        )
