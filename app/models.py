from app import db
from datetime import datetime
from enum import IntEnum, auto
from sqlalchemy_utils import EmailType
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Objects(IntEnum):
    USER = auto()
    SESSION = auto()
    TASK = auto()
    VEHICLE = auto()
    NOTE = auto()
    DELIVERABLE = auto()
    LOCATION = auto()


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    body = db.Column(db.String(10000))
    subject = db.Column(db.String(200))
    task = db.Column(db.Integer, db.ForeignKey('task.id'))
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    session = db.Column(db.Integer, db.ForeignKey('session.id'))
    vehicle = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    deliverable = db.Column(db.Integer, db.ForeignKey('deliverable.id'))

    @property
    def object_type(self):
        return Objects.NOTE

class Deliverable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = db.Column(db.String(64))
    task = db.Column(db.Integer, db.ForeignKey('task.id'))
    notes = db.relationship('Note', backref='deliverable_parent', lazy='dynamic')

    @property
    def object_type(self):
        return Objects.DELIVERABLE

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    line1 = db.Column(db.String(64))
    line2 = db.Column(db.String(64))
    town = db.Column(db.String(64))
    county = db.Column(db.String(64))
    country = db.Column(db.String(64))
    postcode = db.Column(db.String(64))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    pickup_address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dropoff_address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    pickup_address = db.relationship("Address", foreign_keys=[pickup_address_id])
    dropoff_address = db.relationship("Address", foreign_keys=[dropoff_address_id])

    patch = db.Column(db.String(64))
    contact_name = db.Column(db.String(64))
    contact_number = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    final_duration = db.Column(db.Time)
    miles = db.Column(db.Integer)
    flagged_for_deletion = db.Column(db.Boolean, default=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    deliverables = db.relationship('Deliverable', backref='deliverable_task', lazy='dynamic')
    notes = db.relationship('Note', backref='task_parent', lazy='dynamic')

    assigned_rider = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def object_type(self):
        return Objects.TASK

    def __repr__(self):
        return '<Task ID {} taken at {} with priority {}>'.format(str(self.uuid), str(self.timestamp), str(self.priority))


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    manufacturer = db.Column(db.String(64))
    model = db.Column(db.String(64))
    date_of_manufacture = db.Column(db.Date)
    date_of_registration = db.Column(db.Date)
    registration_number = db.Column(db.String(10))
    flagged_for_deletion = db.Column(db.Boolean, default=False)
    notes = db.relationship('Note', backref='vehicle_parent', lazy='dynamic')

    @property
    def object_type(self):
        return Objects.VEHICLE

    def __repr__(self):
        return '<Vehicle {} {} with registration {}>'.format(self.manufacturer, self.model, self.registrationNumber)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    address = db.relationship("Address", foreign_keys=[address_id])
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(EmailType)
    password = db.Column(db.String())
    name = db.Column(db.String(64))
    dob = db.Column(db.Date)
    sessions = db.relationship('Session', backref='coordinator', lazy='dynamic')
    assigned_vehicle = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    patch = db.Column(db.String(64))
    status = db.Column(db.String(64))
    flagged_for_deletion = db.Column(db.Boolean, default=False)
    roles = db.Column(db.String())
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    notes = db.relationship('Note', backref='user_parent', lazy='dynamic')

    tasks = db.relationship('Task', backref='tasks', lazy='dynamic')

    __searchable__ = ['username']

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, _id):
        return cls.query.get(_id)

    @property
    def identity(self):
        return self.id

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @property
    def object_type(self):
        return Objects.USER

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship('Task', backref='sess', lazy='dynamic')
    flagged_for_deletion = db.Column(db.Boolean, default=False)
    notes = db.relationship('Note', backref='session_parent', lazy='dynamic')

    @property
    def object_type(self):
        return Objects.SESSION

    def __repr__(self):
        return '<Session {} {}>'.format(self.uuid, self.timestamp)
    

class DeleteFlags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    object_uuid = db.Column(UUID(as_uuid=True))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    time_to_delete = db.Column(db.Integer)
    time_deleted = db.Column(db.DateTime, index=True)
    object_type = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)


class Location(Address, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64), unique=True)
    contact = db.Column(db.String(64))
    phone_number = db.Column(db.Integer())
    flagged_for_deletion = db.Column(db.Boolean, default=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    address = db.relationship("Address", foreign_keys=[address_id])

    @property
    def object_type(self):
        return Objects.LOCATION
