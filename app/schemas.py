from app import ma
from marshmallow_sqlalchemy import fields, field_for
from marshmallow import post_load
from app import models


class NoteSchema(ma.Schema):
    class Meta:
        model = models.Note
        fields = ('uuid', 'subject', 'body',
                  'task', 'vehicle', 'session',
                  'user', 'deliverable')

    @post_load
    def make_note(self, data):
        return models.Note(**data)


class DeliverableSchema(ma.Schema):
    class Meta:
        model = models.Deliverable
        fields = ('uuid', 'name', 'task', 'notes')

    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'user', 'vehicle', 'session'))

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


class UserSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username', 'address', 'password', 'name', 'email',
                  'dob', 'patch', 'roles', 'notes', 'links')

    username = ma.Str(required=True)
    email = ma.Email()
    dob = ma.DateTime(format='%d/%m/%Y')
    address = fields.fields.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'deliverable', 'vehicle', 'session'))

    links = ma.Hyperlinks(
        {"self": ma.URLFor("user", uuid="<uuid>"), "collection": ma.URLFor("users")}
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


class TaskSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('uuid', 'pickup_address', 'dropoff_address', 'patch', 'contact_name',
                  'contact_number', 'priority', 'session', 'timestamp', 'deliverables', 'notes', 'links')

    contactNumber = ma.Int()

    pickupAddress = fields.fields.Nested(AddressSchema)
    dropoffAddress = fields.fields.Nested(AddressSchema)
    deliverables = fields.fields.Nested(DeliverableSchema, many=True)
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('vehicle', 'user', 'deliverable', 'session'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('task_detail', uuid='<uuid>'),
        'collection': ma.URLFor('tasks_list')
    })

    @post_load
    def make_task(self, data):
        return models.Task(**data)


class SessionSchema(ma.Schema):
    class Meta:
        model = models.Session
        fields = ('uuid', 'user_id',
                  'timestamp', 'tasks',
                  'notes')
    tasks = fields.fields.Nested(TaskSchema, many=True, exclude=('notes', 'deliverables', 'links:self'))
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('vehicle', 'user', 'deliverable', 'task'))


    @post_load
    def make_session(self, data):
        return models.Session(**data)


class VehicleSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'notes', 'links')

    dateOfManufacture = ma.DateTime(format='%d/%m/%Y')
    dateOfRegistration = ma.DateTime(format='%d/%m/%Y')
    registrationNumber = ma.Function(lambda obj: obj.registrationNumber.upper())
    notes = fields.fields.Nested(NoteSchema, many=True, exclude=('task', 'user', 'deliverable', 'session'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', uuid='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    })

    @post_load
    def make_vehicle(self, data):
        return models.Vehicle(**data)

