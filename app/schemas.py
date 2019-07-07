from app import ma
from marshmallow_sqlalchemy import fields, field_for
from marshmallow import post_load
from app import models


class NoteSchema(ma.Schema):
    class Meta:
        model = models.Note
        fields = ('uuid', 'subject', 'body',
                  'task', 'vehicle', 'session',
                  'user', 'deliverable', 'location')

    @post_load
    def make_note(self, data):
        return models.Note(**data)


class DeliverableSchema(ma.Schema):
    class Meta:
        model = models.Deliverable
        fields = ('uuid', 'name', 'task', 'notes')

    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'user', 'vehicle', 'session', 'location'))

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
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('vehicle', 'user', 'deliverable', 'session', 'location'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('task_detail', task_id='<uuid>'),
        'collection': ma.URLFor('tasks_list')
    })

    @post_load
    def make_task(self, data):
        return models.Task(**data)


class UserSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username', 'address', 'password', 'name', 'email',
                  'dob', 'patch', 'roles', 'notes', 'links', 'tasks')

    username = ma.Str(required=True)
    email = ma.Email()
    dob = ma.DateTime(format='%d/%m/%Y')
    address = fields.fields.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session', 'location'))
    tasks = fields.fields.Nested(TaskSchema, many=True)

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
                  'notes')
    tasks = fields.fields.Nested(TaskSchema, many=True, exclude=('notes', 'deliverables'))
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('vehicle', 'user', 'deliverable', 'task', 'location'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('session_detail', session_id='<uuid>'),
        'collection': ma.URLFor('sessions_list')
    })

    @post_load
    def make_session(self, data):
        return models.Session(**data)


class VehicleSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'notes', 'links')

    date_of_manufacture = ma.DateTime(format='%d/%m/%Y')
    date_of_registration = ma.DateTime(format='%d/%m/%Y')
    registration_number = ma.Function(lambda obj: obj.registrationNumber.upper())
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'user', 'deliverable', 'session', 'location'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', vehicle_id='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    })

    @post_load
    def make_vehicle(self, data):
        return models.Vehicle(**data)


class LocationSchema(ma.Schema):
    class Meta:
        model = models.Location
        fields = ('name', 'contact', 'phone_number', 'address', 'notes', 'links')

    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'user', 'deliverable', 'session', 'vehicle'))
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
