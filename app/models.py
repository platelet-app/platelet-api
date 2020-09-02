import redis
from redis import Connection
from rq import Queue

from app import db, socketio
from datetime import datetime
from enum import IntEnum, auto
from sqlalchemy_utils import EmailType
from app.search import add_to_index, remove_from_index, query_index
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Objects(IntEnum):
    USER = auto()
    SESSION = auto()
    TASK = auto()
    VEHICLE = auto()
    COMMENT = auto()
    DELIVERABLE = auto()
    DELIVERABLE_TYPE = auto()
    LOCATION = auto()
    PRIORITY = auto()
    PATCH = auto()
    DELETE_FLAG = auto()
    SETTINGS = auto()
    UNKNOWN = auto()
    

class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total['value'] == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)


    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


class SocketsMixin:
    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SocketsMixin):
                socketio.emit('subscribed_response', {'object_uuid': str(obj.uuid)}, room=str(obj.uuid), namespace="/socket")
        for obj in session._changes['update']:
            if isinstance(obj, SocketsMixin):
                socketio.emit('subscribed_response', {'object_uuid': str(obj.uuid)}, room=str(obj.uuid), namespace="/socket")
        for obj in session._changes['delete']:
            if isinstance(obj, SocketsMixin):
                socketio.emit('subscribed_response', {'object_uuid': str(obj.uuid)}, room=str(obj.uuid), namespace="/socket")

        session._changes = None


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class CommonMixin:
    time_created = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow)
    time_modified = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    flagged_for_deletion = db.Column(db.Boolean, default=False)


class ServerSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow)
    time_modified = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    organisation_name = db.Column(db.String, unique=True)
    image_url = db.Column(db.String)
    version = db.Column(db.String)
    hostname = db.Column(db.String)
    favicon = db.Column(db.String)

    locale_id = db.Column(db.Integer, db.ForeignKey('locale.id'))
    locale = db.relationship("Locale",  foreign_keys=[locale_id])

    @property
    def object_type(self):
        return Objects.SETTINGS


class Locale(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, unique=True)
    code = db.Column(db.String, unique=True)


class Comment(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    body = db.Column(db.String(10000))
    author_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.uuid'))
    author = db.relationship("User", foreign_keys=[author_uuid])
    parent_type = db.Column(db.Integer)
    parent_uuid = db.Column(UUID(as_uuid=True))
    publicly_visible = db.Column(db.Boolean, default=True)

    @property
    def object_type(self):
        return Objects.COMMENT


class DeliverableType(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, unique=True)

    @property
    def object_type(self):
        return Objects.DELIVERABLE_TYPE


class Deliverable(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    task_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('task.uuid'))
    type_id = db.Column(db.Integer, db.ForeignKey('deliverable_type.id'))
    type = db.relationship("DeliverableType", foreign_keys=[type_id])

    @property
    def object_type(self):
        return Objects.DELIVERABLE


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    ward = db.Column(db.String(64))
    line1 = db.Column(db.String(64))
    line2 = db.Column(db.String(64))
    town = db.Column(db.String(64))
    county = db.Column(db.String(64))
    country = db.Column(db.String(64))
    postcode = db.Column(db.String(64))
    what3words = db.Column(db.String(64))


class Priority(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64), unique=True)

    @property
    def object_type(self):
        return Objects.PRIORITY


#class TaskParent(db.Model, CommonMixin, SocketsMixin):
#    id = db.Column(db.Integer, primary_key=True)
#    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)


task_rider_assignees = db.Table(
    'task_rider_assignees',
    db.Column('task_uuid', UUID(as_uuid=True), db.ForeignKey('task.uuid'), primary_key=True),
    db.Column('user_uuid', UUID(as_uuid=True), db.ForeignKey('user.uuid'), primary_key=True)
)

task_coordinator_assignees = db.Table(
    'task_coordinator_assignees',
    db.Column('task_uuid', UUID(as_uuid=True), db.ForeignKey('task.uuid'), primary_key=True),
    db.Column('user_uuid', UUID(as_uuid=True), db.ForeignKey('user.uuid'), primary_key=True)
)


class Task(SearchableMixin, db.Model, CommonMixin, SocketsMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    author_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.uuid'))
    author = db.relationship("User", foreign_keys=[author_uuid])
    time_of_call = db.Column(db.DateTime(timezone=True), index=True)

    time_picked_up = db.Column(db.DateTime(timezone=True))
    time_dropped_off = db.Column(db.DateTime(timezone=True))

    time_cancelled = db.Column(db.DateTime(timezone=True))
    time_rejected = db.Column(db.DateTime(timezone=True))

    pickup_address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dropoff_address_id = db.Column(db.Integer, db.ForeignKey('address.id'))

    pickup_address = db.relationship("Address", foreign_keys=[pickup_address_id])
    dropoff_address = db.relationship("Address", foreign_keys=[dropoff_address_id])

    ## TODO: figure out how to add more than one signature for relays
   # destination_contact_name = db.Column(db.String(64))
   # destination_contact_number = db.Column(db.String(64))

   # recipient_name = db.Column(db.String(64))
   # recipient_signature = db.Column(db.String(4096))

   # sender_name = db.Column(db.String(64))
   # sender_signature = db.Column(db.String(4096))

    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    patch = db.relationship("Patch", foreign_keys=[patch_id])
    contact_name = db.Column(db.String(64))
    contact_number = db.Column(db.String(64))
    patient_name = db.Column(db.String(64))
    patient_contact_number = db.Column(db.String(64))
    destination_contact_name = db.Column(db.String(64))
    destination_contact_number = db.Column(db.String(64))
    final_duration = db.Column(db.Time)
    miles = db.Column(db.Integer)
    priority_id = db.Column(db.Integer, db.ForeignKey('priority.id'))
    priority = db.relationship("Priority", foreign_keys=[priority_id])
    deliverables = db.relationship('Deliverable', backref='deliverable_task', lazy='dynamic')
    assigned_riders = db.relationship('User', secondary=task_rider_assignees, lazy='subquery',
        backref=db.backref('tasks', lazy=True))

    assigned_coordinators = db.relationship('User', secondary=task_coordinator_assignees, lazy='subquery',
                                    backref=db.backref('tasks_as_coordinator', lazy=True))

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Task.uuid)".format(Objects.TASK)
    )

    __searchable__ = ['contact_name', 'contact_number', 'session_uuid']

    @property
    def object_type(self):
        return Objects.TASK

    def __repr__(self):
        return '<Task ID {} taken at {} with priority {}>'.format(str(self.uuid), str(self.time_created),
                                                                  str(self.priority))


class Vehicle(SearchableMixin, db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True)
    manufacturer = db.Column(db.String(64))
    model = db.Column(db.String(64))
    date_of_manufacture = db.Column(db.Date)
    date_of_registration = db.Column(db.Date)
    registration_number = db.Column(db.String(10))
    assigned_user_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.uuid'))

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Vehicle.uuid)".format(Objects.VEHICLE)
    )

    __searchable__ = ['manufacturer', 'model', 'registration_number', 'name']

    @property
    def object_type(self):
        return Objects.VEHICLE

    def __repr__(self):
        return '<Vehicle {} {} with registration {}>'.format(self.manufacturer, self.model, self.registration_number)


class User(SearchableMixin, db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    address = db.relationship("Address", foreign_keys=[address_id])

    username = db.Column(db.String(64), unique=True)
    email = db.Column(EmailType)
    password = db.Column(db.String())
    contact_number = db.Column(db.String(64))
    name = db.Column(db.String(64))
    display_name = db.Column(db.String(64), unique=True)
    dob = db.Column(db.Date)
    assigned_vehicles = db.relationship('Vehicle', backref='assigned_user', lazy='dynamic')

    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    patch = db.relationship("Patch", foreign_keys=[patch_id])

    status = db.Column(db.String(64))
    roles = db.Column(db.String())
    is_active = db.Column(db.Boolean, default=True, server_default='true')

    #tasks = db.relationship('Task', backref='rider', lazy='dynamic')
    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == User.uuid)".format(Objects.USER)
    )
    password_reset_on_login = db.Column(db.Boolean, default=False)

    __searchable__ = ['username', 'roles', 'name', 'email']

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


session_collaborators = db.Table(
    'session_collaborators',
    db.Column('session_uuid', UUID(as_uuid=True), db.ForeignKey('session.uuid'), primary_key=True),
    db.Column('user_uuid', UUID(as_uuid=True), db.ForeignKey('user.uuid'), primary_key=True)
)


class Session(SearchableMixin, db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    coordinator_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.uuid'))
    collaborators = db.relationship('User', secondary=session_collaborators, lazy='subquery',
                                     backref=db.backref('acollaborator_sessions', lazy=True))
    #tasks = db.relationship('Task', backref='parent_session', lazy='dynamic')

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Session.uuid)".format(Objects.SESSION)
    )
    __searchable__ = ['time_created']

    @property
    def task_count(self):
        return len([task for task in self.tasks.all() if not task.flagged_for_deletion])

    @property
    def object_type(self):
        return Objects.SESSION

    def __repr__(self):
        return '<Session {} {}>'.format(self.uuid, self.time_created)


class DeleteFlags(SearchableMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), nullable=False)
    object_uuid = db.Column(UUID(as_uuid=True))
    time_created = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow)
    time_to_delete = db.Column(db.Integer)
    time_deleted = db.Column(db.DateTime(timezone=True), index=True)
    object_type = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)

    __searchable__ = ['object_uuid', 'object_type', 'active']


class Location(SearchableMixin, db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True)
    contact_name = db.Column(db.String(64))
    contact_number = db.Column(db.String(64))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    address = db.relationship("Address", foreign_keys=[address_id])

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Location.uuid)".format(Objects.LOCATION)
    )

    __searchable__ = ['name', 'contact_name', 'contact_number', 'address']

    @property
    def object_type(self):
        return Objects.LOCATION


class Patch(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, unique=True)

    @property
    def object_type(self):
        return Objects.PATCH
