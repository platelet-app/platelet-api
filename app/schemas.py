from marshmallow import ValidationError

from app import ma
from marshmallow_sqlalchemy import fields, field_for
from marshmallow import post_load
from app import models
import datetime


class NoteSchema(ma.Schema):
    class Meta:
        model = models.Note
        fields = ('subject', 'body',
                  'task', 'vehicle', 'session',
                  'user', 'deliverable', 'location')

    @post_load
    def make_note(self, data):
        return models.Note(**data)


class DeliverableSchema(ma.Schema):
    class Meta:
        model = models.Deliverable
        fields = ('uuid', 'name', 'task_id', 'notes')

    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location', 'user'))

    @post_load
    def make_deliverable(self, data):
        return models.Deliverable(**data)


class AddressSchema(ma.Schema):
    class Meta:
        model = models.Address

        fields = ('line1', 'line2', 'town',
                  'county', 'country', 'postcode')

    postcode = ma.Function(lambda obj: obj.postcode.upper())

    @post_load
    def make_address(self, data):
        return models.Address(**data)


class TaskSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('uuid', 'pickup_address', 'dropoff_address', 'patch', 'contact_name',
                  'contact_number', 'priority', 'session_id', 'timestamp', 'deliverables',
                  'notes', 'links', 'assigned_rider')

    contactNumber = ma.Int()

    pickup_address = fields.fields.Nested(AddressSchema)
    dropoff_address = fields.fields.Nested(AddressSchema)
    deliverables = fields.fields.Nested(DeliverableSchema, many=True)
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location', 'user'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('task_detail', task_id='<uuid>'),
        'collection': ma.URLFor('tasks_list')
    })

    @post_load
    def make_task(self, data):
        return models.Task(**data)


class VehicleSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'notes', 'links', 'name')

    date_of_manufacture = ma.DateTime(format='%d/%m/%Y')
    date_of_registration = ma.Function(lambda obj: validate_date_of_registration(obj))
    registration_number = ma.Function(lambda obj: obj.registrationNumber.upper())
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location', 'user'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', vehicle_id='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    })

    @post_load
    def make_vehicle(self, data):
        return models.Vehicle(**data)

def validate_date_of_registration(obj):
    try:
        datetime.datetime.strptime(obj.dateOfRegistration, '%d/%m/%Y')
    except ValueError:
        raise ValidationError("{} has invalid date format, should be %d/%m/%Y".format(obj.dateOfRegistration))

    if obj.dateOfManufacture > obj.dateOfRegistration:
        raise ValidationError("date of registration cannot be before date of manufacture")


class UserSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username', 'address', 'password', 'name', 'email',
                  'dob', 'patch', 'roles', 'notes', 'links', 'tasks', 'vehicle')

    username = ma.Str(required=True)
    email = ma.Email()
    dob = ma.DateTime(format='%d/%m/%Y')
    address = fields.fields.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location', 'user'))
    tasks = fields.fields.Nested(TaskSchema, many=True)
    vehicle = fields.fields.Nested(VehicleSchema, dump_only=True)

    links = ma.Hyperlinks(
        {"self": ma.URLFor("user", user_id="<uuid>"), "collection": ma.URLFor("users")}
    )

    @post_load
    def make_user(self, data):
        return models.User(**data)


class UserUsernameSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username')

    username = ma.Str(required=True)


class UserAddressSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'name', 'address')

    postcode = ma.Function(lambda obj: obj.postcode.upper())
    address = fields.fields.Nested(AddressSchema)



class SessionSchema(ma.Schema):
    class Meta:
        model = models.Session
        fields = ('uuid', 'user_id',
                  'timestamp', 'tasks',
                  'notes', 'links')
    tasks = fields.fields.Nested(TaskSchema, dump_only=True, many=True, exclude=('notes', 'deliverables', 'pickup_address', 'dropoff_address'))
    notes = fields.fields.Nested(NoteSchema, dump_only=True, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location', 'user'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('session_detail', session_id='<uuid>'),
        'collection': ma.URLFor('sessions_list')
    })

    @post_load
    def make_session(self, data):
        return models.Session(**data)


class LocationSchema(ma.Schema):
    class Meta:
        model = models.Location
        fields = ('name', 'contact', 'phone_number', 'address', 'notes', 'links')

    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location', 'user'))
    address = fields.fields.Nested(AddressSchema)

    links = ma.Hyperlinks({
        'self': ma.URLFor('location_detail', location_id='<uuid>'),
        'collection': ma.URLFor('location_list')
    })

    @post_load
    def make_location(self, data):
        return models.Location(**data)

class SearchSchema(ma.Schema):
    class Meta:
        fields = ('query', 'type', 'page')
