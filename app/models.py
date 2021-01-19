import redis
from flask_sqlalchemy import BaseQuery
from redis import Connection
from rq import Queue
from sqlalchemy.ext.associationproxy import association_proxy

from app import db
from datetime import datetime
from enum import IntEnum, auto
from sqlalchemy_utils import EmailType
from app.search import add_to_index, remove_from_index, query_index
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Objects(IntEnum):
    USER = auto()
    TASK = auto()
    TASK_PARENT = auto()
    VEHICLE = auto()
    COMMENT = auto()
    DELIVERABLE = auto()
    DELIVERABLE_TYPE = auto()
    LOCATION = auto()
    PRIORITY = auto()
    PATCH = auto()
    DELETE_FLAG = auto()
    SETTINGS = auto()
    LOG_ENTRY = auto()
    UNKNOWN = auto()


class QueryWithSoftDelete(BaseQuery):
    _with_deleted = False

    def __new__(cls, *args, **kwargs):
        obj = super(QueryWithSoftDelete, cls).__new__(cls)
        obj._with_deleted = kwargs.pop('_with_deleted', False)
        if len(args) > 0:
            super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)
            return obj.filter_by(deleted=False) if not obj._with_deleted else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_deleted(self):
        return self.__class__(db.class_mapper(self._mapper_zero().class_),
                              session=db.session(), _with_deleted=True)

    def _get(self, *args, **kwargs):
        # this calls the original query.get function from the base class
        return super(QueryWithSoftDelete, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        # the query.get method does not like it if there is a filter clause
        # pre-loaded, so we need to implement it using a workaround
        obj = self.with_deleted()._get(*args, **kwargs)
        return obj if obj is None or self._with_deleted or not obj.deleted else None


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
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
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class CommonMixin:
    time_created = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow)
    time_modified = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)


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
    locale = db.relationship("Locale", foreign_keys=[locale_id])

    @property
    def object_type(self):
        return Objects.SETTINGS


class Locale(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, unique=True)
    code = db.Column(db.String, unique=True)

    query_class = QueryWithSoftDelete


class Comment(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    body = db.Column(db.String(10000))
    author_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.uuid'))
    author = db.relationship("User", foreign_keys=[author_uuid])
    parent_type = db.Column(db.Integer)
    parent_uuid = db.Column(UUID(as_uuid=True))
    publicly_visible = db.Column(db.Boolean, default=True)

    logged_actions = db.relationship(
        'LogEntry',
        primaryjoin="and_(LogEntry.parent_type == {}, foreign(LogEntry.parent_uuid) == Comment.uuid)".format(
            Objects.COMMENT)
    )

    query_class = QueryWithSoftDelete

    @property
    def object_type(self):
        return Objects.COMMENT


class DeliverableType(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, unique=True)

    query_class = QueryWithSoftDelete

    @property
    def object_type(self):
        return Objects.DELIVERABLE_TYPE


class Deliverable(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    task_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('task.uuid'))
    type_id = db.Column(db.Integer, db.ForeignKey('deliverable_type.id'))
    type = db.relationship("DeliverableType", foreign_keys=[type_id])

    logged_actions = db.relationship(
        'LogEntry',
        primaryjoin="and_(LogEntry.parent_type == {}, foreign(LogEntry.parent_uuid) == Deliverable.uuid)".format(
            Objects.DELIVERABLE)
    )

    query_class = QueryWithSoftDelete

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

    query_class = QueryWithSoftDelete

    @property
    def object_type(self):
        return Objects.PRIORITY


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


class TasksParent(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    relays_with_deleted_cancelled_rejected = db.relationship(
        'Task',
        primaryjoin="foreign(Task.parent_id) == TasksParent.id",
        lazy="dynamic"
    )

    reference = db.Column(db.String(32))

    query_class = QueryWithSoftDelete


class Task(SearchableMixin, db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    parent_id = db.Column(db.Integer, db.ForeignKey(TasksParent.id), nullable=False)
    parent = db.relationship(
        TasksParent,
        foreign_keys=[parent_id],
        backref=db.backref(
            'relays',
            primaryjoin='and_('
                        'foreign(Task.parent_id)==TasksParent.id,'
                        'Task.deleted.isnot(True),'
                        'Task.time_cancelled.is_(None),'
                        'Task.time_rejected.is_(None))',
            lazy='dynamic')
    )
    reference = association_proxy("parent", "reference")
    order_in_relay = db.Column(db.Integer, nullable=False)
    author_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey("user.uuid"))
    author = db.relationship("User", foreign_keys=[author_uuid], backref=db.backref("tasks_as_author", lazy="dynamic"))
    time_of_call = db.Column(db.DateTime(timezone=True), index=True)

    requester_contact_id = db.Column(db.Integer, db.ForeignKey("contact.id"))
    requester_contact = db.relationship("Contact", foreign_keys=[requester_contact_id])

    time_picked_up = db.Column(db.DateTime(timezone=True))
    time_dropped_off = db.Column(db.DateTime(timezone=True))

    time_cancelled = db.Column(db.DateTime(timezone=True))
    time_rejected = db.Column(db.DateTime(timezone=True))

    saved_location_pickup_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey("location.uuid"))
    saved_location_pickup = db.relationship("Location", foreign_keys=[saved_location_pickup_uuid], backref=db.backref("linked_tasks_as_pickup", lazy="dynamic"))

    saved_location_dropoff_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey("location.uuid"))
    saved_location_dropoff = db.relationship("Location", foreign_keys=[saved_location_dropoff_uuid], backref=db.backref("linked_tasks_as_dropoff", lazy="dynamic"))

    pickup_address_id = db.Column(db.Integer, db.ForeignKey("address.id"))
    dropoff_address_id = db.Column(db.Integer, db.ForeignKey("address.id"))

    pickup_address = db.relationship("Address", foreign_keys=[pickup_address_id])
    dropoff_address = db.relationship("Address", foreign_keys=[dropoff_address_id])

    ## TODO: figure out how to add more than one signature for relays
    # destination_contact_name = db.Column(db.String(64))
    # destination_contact_number = db.Column(db.String(64))

    # recipient_name = db.Column(db.String(64))
    # recipient_signature = db.Column(db.String(4096))

    # sender_name = db.Column(db.String(64))
    # sender_signature = db.Column(db.String(4096))

    patch_id = db.Column(db.Integer, db.ForeignKey("patch.id"))
    patch = db.relationship("Patch", foreign_keys=[patch_id])
    final_duration = db.Column(db.Time)
    miles = db.Column(db.Integer)
    priority_id = db.Column(db.Integer, db.ForeignKey("priority.id"), nullable=True)
    priority = db.relationship("Priority", foreign_keys=[priority_id])
    deliverables = db.relationship("Deliverable", backref="deliverable_task", lazy="dynamic")
    assigned_riders = db.relationship(
        'User',
        secondary=task_rider_assignees,
        lazy='dynamic',
        backref=db.backref(
            'tasks_as_rider',
            lazy='dynamic'))

    assigned_coordinators = db.relationship(
        'User',
        secondary=task_coordinator_assignees,
        lazy='dynamic',
        backref=db.backref(
            'tasks_as_coordinator',
            lazy='dynamic'))

    relay_previous_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey(uuid))
    relay_previous = db.relationship(
        "Task",
        uselist=False,
        foreign_keys=[relay_previous_uuid],
        remote_side=[uuid],
        backref=db.backref('relay_next', uselist=False))

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Task.uuid)".format(Objects.TASK)
    )

    logged_actions = db.relationship(
        'LogEntry',
        primaryjoin="and_(LogEntry.parent_type == {}, foreign(LogEntry.parent_uuid) == Task.uuid)".format(Objects.TASK)
    )

    __searchable__ = [
        'reference',
        'uuid',
    ]

    query_class = QueryWithSoftDelete

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
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Vehicle.uuid)".format(
            Objects.VEHICLE)
    )

    logged_actions = db.relationship(
        'LogEntry',
        primaryjoin="and_(LogEntry.parent_type == {}, foreign(LogEntry.parent_uuid) == Vehicle.uuid)".format(
            Objects.VEHICLE)
    )

    __searchable__ = ['manufacturer', 'model', 'registration_number', 'name']
    query_class = QueryWithSoftDelete

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

    # profile pictures
    profile_picture_key = db.Column(db.String(128))
    profile_picture_thumbnail_key = db.Column(db.String(128))

    password_reset_on_login = db.Column(db.Boolean, default=False)

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == User.uuid)".format(Objects.USER)
    )

    logged_actions = db.relationship(
        'LogEntry',
        primaryjoin="and_(LogEntry.parent_type == {}, foreign(LogEntry.parent_uuid) == User.uuid)".format(Objects.USER)
    )

    __searchable__ = ['username', 'roles', 'name', 'email']
    query_class = QueryWithSoftDelete

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


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    address = db.relationship("Address", foreign_keys=[address_id])
    telephone_number = db.Column(db.String(64), nullable=True)
    mobile_number = db.Column(db.String(64), nullable=True)
    email_address = db.Column(db.String(128), nullable=True)


class Location(SearchableMixin, db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    contact = db.relationship("Contact", foreign_keys=[contact_id])
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    address = db.relationship("Address", foreign_keys=[address_id])

    comments = db.relationship(
        'Comment',
        primaryjoin="and_(Comment.parent_type == {}, foreign(Comment.parent_uuid) == Location.uuid)".format(
            Objects.LOCATION)
    )

    logged_actions = db.relationship(
        'LogEntry',
        primaryjoin="and_(LogEntry.parent_type == {}, foreign(LogEntry.parent_uuid) == Location.uuid)".format(
            Objects.LOCATION)
    )

    __searchable__ = ['name', 'contact_name', 'contact_number', 'address']
    query_class = QueryWithSoftDelete

    @property
    def object_type(self):
        return Objects.LOCATION


class Patch(db.Model, CommonMixin):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, unique=True)

    query_class = QueryWithSoftDelete

    @property
    def object_type(self):
        return Objects.PATCH


class HTTPRequestType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(32), unique=True)

    @property
    def object_type(self):
        return Objects.HTTP_REQUEST_TYPE


class HTTPResponseStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer)
    status_description = db.Column(db.String(64))
    status_type = db.Column(db.String(64))


class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    time_created = db.Column(db.DateTime(timezone=True), index=True, default=datetime.utcnow)
    ip_address = db.Column(db.String)
    parent_type = db.Column(db.Integer)
    parent_uuid = db.Column(UUID(as_uuid=True))
    calling_user_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('user.uuid'))
    data_fields = db.Column(db.String())
    calling_user = db.relationship(
        "User",
        foreign_keys=[calling_user_uuid],
        backref='user_actions')
    http_request_type_id = db.Column(db.Integer, db.ForeignKey(HTTPRequestType.id))
    http_request_type = db.relationship(
        HTTPRequestType,
        foreign_keys=[http_request_type_id],
        backref=db.backref('logs', lazy='dynamic'))
    http_response_status_id = db.Column(db.Integer, db.ForeignKey(HTTPResponseStatus.id))
    http_response_status = db.relationship(
        HTTPResponseStatus,
        foreign_keys=[http_response_status_id],
        backref=db.backref('logs', lazy='dynamic'))

    @property
    def object_type(self):
        return Objects.LOG_ENTRY
