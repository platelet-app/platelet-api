from marshmallow import ValidationError, pre_load
from app import ma
from marshmallow_sqlalchemy import fields, field_for
from app import models
import datetime

class TimesMixin:
    time_created = fields.fields.DateTime()
    time_modified = fields.fields.DateTime()

class NoteSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.Note
        fields = ('uuid', 'subject', 'body',
                  'task_uuid', 'vehicle_uuid', 'session_uuid',
                  'user_uuid', 'deliverable_uuid', 'location_uuid',
                  "time_created", "time_modified")


class DeliverableTypeSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.DeliverableType
        fields = ('id', 'name')


class DeliverableSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.Deliverable
        fields = ('uuid', 'task_uuid', 'notes', 'type', 'type_id',
                  "time_created", "time_modified")

    notes = fields.fields.Nested(NoteSchema, many=True,
                                 exclude=('task_uuid', 'deliverable_uuid', 'vehicle_uuid', 'session_uuid', 'location_uuid', 'user_uuid'))
    type = fields.fields.Nested(DeliverableTypeSchema, only="name")


class AddressSchema(ma.ModelSchema):
    class Meta:
        model = models.Address

        fields = ('ward', 'line1', 'line2', 'town',
                  'county', 'country', 'postcode',
                  'what3words')

    postcode = ma.Function(lambda obj: obj.postcode.upper())


class PatchSchema(ma.ModelSchema):
    class Meta:
        model = models.Patch
        fields = ('id', 'label')


class UserSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.User
        fields = ('uuid', 'username', 'address', 'password', 'name', 'email',
                  'dob', 'patch', 'roles', 'notes', 'links', 'display_name',
                  'assigned_vehicles', 'patch_id',
                  "time_created", "time_modified")

    username = ma.Str(required=True)
    email = ma.Email()
    dob = ma.DateTime(format='%d/%m/%Y')
    address = fields.fields.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    assigned_vehicles = fields.fields.Nested("VehicleSchema", many=True, dump_only=True, exclude=("assigned_user",))
    notes = fields.fields.Nested(NoteSchema, many=True,
                                 exclude=('task_uuid', 'deliverable_uuid', 'vehicle_uuid', 'session_uuid', 'location_uuid', 'user_uuid'))
    #tasks = fields.fields.Nested(TaskSchema, many=True)
    #vehicle = fields.fields.Nested(VehicleSchema, dump_only=True)

    links = ma.Hyperlinks(
        {"self": ma.URLFor("user", user_id="<uuid>"), "collection": ma.URLFor("users")}
    )

    patch = fields.fields.Nested(PatchSchema, only="label", dump_only=True)


class VehicleSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.Vehicle
        fields = ('manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'notes', 'links', 'name', 'assigned_user', 'assigned_user_uuid', 'uuid',
                  "time_created", "time_modified")

    date_of_manufacture = ma.DateTime(format='%d/%m/%Y')
    date_of_registration = ma.Function(lambda obj: validate_date_of_registration(obj))
    assigned_user = fields.fields.Nested(UserSchema, dump_only=True)
    #registration_number = ma.Function(lambda obj: obj.registrationNumber.upper())
    notes = fields.fields.Nested(NoteSchema, many=True,
                                 exclude=('task_uuid', 'deliverable_uuid', 'vehicle_uuid', 'session_uuid', 'location_uuid', 'user_uuid'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', vehicle_id='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    })


def validate_date_of_registration(obj):
    try:
        datetime.datetime.strptime(obj.dateOfRegistration, '%d/%m/%Y')
    except ValueError:
        raise ValidationError("{} has invalid date format, should be %d/%m/%Y".format(obj.dateOfRegistration))

    if obj.dateOfManufacture > obj.dateOfRegistration:
        raise ValidationError("date of registration cannot be before date of manufacture")



class PrioritySchema(ma.ModelSchema):
    class Meta:
        model = models.Priority
        fields = ('id', 'label')


class TaskSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.Task
        fields = ('uuid', 'pickup_address', 'dropoff_address', 'patch', 'patch_id', 'contact_name',
                  'contact_number', 'priority', 'session_uuid', 'time_of_call', 'deliverables',
                  'notes', 'links', 'assigned_rider', 'time_picked_up', 'time_dropped_off', 'rider',
                  'priority_id', 'time_cancelled', 'time_rejected', "patient_name", "patient_contact_number",
                  "destination_contact_number", "destination_contact_name",
                  "time_created", "time_modified")

    pickup_address = fields.fields.Nested(AddressSchema)
    dropoff_address = fields.fields.Nested(AddressSchema)
    rider = fields.fields.Nested(UserSchema, exclude=('uuid', 'address', 'password', 'email', 'dob', 'roles', 'notes'), dump_only=True)
    deliverables = fields.fields.Nested(DeliverableSchema, many=True)
    notes = fields.fields.Nested(NoteSchema, many=True,
                                 exclude=('task_uuid', 'deliverable_uuid', 'vehicle_uuid', 'session_uuid', 'location_uuid', 'user_uuid'))
    pickup_time = fields.fields.DateTime(allow_none=True)
    time_dropped_off = fields.fields.DateTime(allow_none=True)
    time_cancelled = fields.fields.DateTime(allow_none=True)
    time_rejected = fields.fields.DateTime(allow_none=True)
    priority = fields.fields.Nested(PrioritySchema, only="label", dump_only=True)
    patch = fields.fields.Nested(PatchSchema, only="label", dump_only=True)
    time_of_call = fields.fields.DateTime()

    links = ma.Hyperlinks({
        'self': ma.URLFor('task_detail', task_id='<uuid>'),
        'collection': ma.URLFor('tasks_list')
    })

#    @pre_load
#    def set_urgency(self, data, **kwargs):
#        if "priority" in data:



class UserUsernameSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username')

    username = ma.Str(required=True)


class UserAddressSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('uuid', 'name', 'address')

    postcode = ma.Function(lambda obj: obj.postcode.upper())
    address = fields.fields.Nested(AddressSchema, exclude=("ward",))


class SessionSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.Session
        fields = ('uuid', 'user_uuid',
                  'time_created', 'tasks',
                  'notes', 'links', 'task_count',
                  "time_created", "time_modified")

    tasks = fields.fields.Nested(TaskSchema, dump_only=True, many=True,
                                 exclude=('notes', 'deliverables'))
    notes = fields.fields.Nested(NoteSchema, dump_only=True, many=True,
                                 exclude=('task_uuid', 'deliverable_uuid', 'vehicle_uuid', 'session_uuid', 'location_uuid', 'user_uuid'))

    links = ma.Hyperlinks({
        'self': ma.URLFor('session_detail', session_id='<uuid>'),
        'collection': ma.URLFor('sessions_list')
    })


class LocationSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.Location
        fields = ('uuid', 'name', 'contact_name', 'contact_number', 'address', 'notes', 'links',
                  "time_created", "time_modified")

    notes = fields.fields.Nested(NoteSchema, many=True,
                                 exclude=('task_uuid', 'deliverable_uuid', 'vehicle_uuid', 'session_uuid', 'location_uuid', 'user_uuid'))
    address = fields.fields.Nested(AddressSchema)

    links = ma.Hyperlinks({
        'self': ma.URLFor('location_detail', location_id='<uuid>'),
        'collection': ma.URLFor('location_list')
    })


class SearchSchema(ma.ModelSchema):
    class Meta:
        fields = ('query', 'type', 'page')
