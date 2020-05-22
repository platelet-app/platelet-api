from marshmallow import ValidationError, pre_dump, post_dump
from app.exceptions import ObjectNotFoundError
from marshmallow_sqlalchemy import fields, field_for
from app import models, ma, flask_version
import datetime
from app.utilities import get_object, calculate_tasks_etag


class TimesMixin:
    time_created = fields.fields.DateTime(dump_only=True)
    time_modified = fields.fields.DateTime(dump_only=True)


class DeleteFilterMixin:
    @pre_dump(pass_many=True)
    def filter_deleted(self, data, many):
        if many:
            return list(filter(lambda t: not t.flagged_for_deletion, data))
        else:
            if data.flagged_for_deletion:
                raise ObjectNotFoundError
            else:
                return data


class ServerSettingsSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.ServerSettings
        fields = ('organisation_name', 'image_url',
                  'version', 'hostname', 'favicon', 'locale',
                  'locale_id')

    locale = fields.fields.Nested('LocaleSchema', dump_only=True, exclude=('id',))

    @post_dump()
    def flask_version(self, data):
        data['flask_version'] = flask_version
        return data


class LocaleSchema(ma.ModelSchema):
    class Meta:
        model = models.Locale
        fields = ('label', 'id', 'code')


class CommentSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.Comment
        fields = ('uuid', 'body', 'author', 'parent_uuid', 'author_uuid',
                  "time_created", "time_modified", "publicly_visible")
    author = fields.fields.Nested(
        'UserSchema', dump_only=True,
        exclude=('username', 'address', 'password', 'name', 'email',
                 'dob', 'patch', 'roles', 'comments', 'assigned_vehicles', 'patch_id',
                 "time_created", "time_modified"))


class DeliverableTypeSchema(ma.ModelSchema, TimesMixin):
    class Meta:
        model = models.DeliverableType
        fields = ('id', 'label')


class DeliverableSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.Deliverable
        fields = ('uuid', 'task_uuid', 'comments', 'type', 'type_id',
                  "time_created", "time_modified")

    comments = fields.fields.Nested(CommentSchema, dump_only=True, many=True)
    type = fields.fields.Nested(DeliverableTypeSchema, dump_only=True, only="label")


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


class UserSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.User
        fields = ('uuid', 'username', 'address', 'password', 'name', 'email',
                  'dob', 'patch', 'roles', 'comments', 'links', 'display_name',
                  'assigned_vehicles', 'patch_id', 'contact_number',
                  "time_created", "time_modified")

    username = ma.Str(required=True)
    email = ma.Email()
    dob = ma.DateTime(format='%d/%m/%Y')
    address = fields.fields.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    assigned_vehicles = fields.fields.Nested("VehicleSchema", many=True, dump_only=True, exclude=("assigned_user",))
    comments = fields.fields.Nested(CommentSchema, dump_only=True, many=True)
    #tasks = fields.fields.Nested(TaskSchema, many=True)
    #vehicle = fields.fields.Nested(VehicleSchema, dump_only=True)

    links = ma.Hyperlinks(
        {"self": ma.URLFor("user", user_id="<uuid>"), "collection": ma.URLFor("users")}
    )

    patch = fields.fields.Nested(PatchSchema, only="label", dump_only=True)


class VehicleSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.Vehicle
        fields = ('uuid', 'manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'comments', 'links', 'name', 'assigned_user', 'assigned_user_uuid',
                  "time_created", "time_modified")

    date_of_manufacture = fields.fields.DateTime(format='%d/%m/%Y')
    date_of_registration = ma.Function(lambda obj: validate_date_of_registration(obj))
    assigned_user = fields.fields.Nested(UserSchema, dump_only=True)
    assigned_user_uuid = fields.fields.String(allow_none=True)
    #registration_number = ma.Function(lambda obj: obj.registrationNumber.upper())
    comments = fields.fields.Nested(CommentSchema, dump_only=True, many=True)
    uuid = fields.fields.String(dump_only=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', vehicle_id='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    }, dump_only=True)


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


class TaskSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.Task
        fields = ('uuid', 'pickup_address', 'dropoff_address', 'patch', 'patch_id', 'contact_name',
                  'contact_number', 'priority', 'session_uuid', 'time_of_call', 'deliverables',
                  'comments', 'links', 'assigned_rider', 'time_picked_up', 'time_dropped_off', 'rider',
                  'priority_id', 'time_cancelled', 'time_rejected', "patient_name", "patient_contact_number",
                  "destination_contact_number", "destination_contact_name",
                  "time_created", "time_modified", "assigned_users")

    pickup_address = fields.fields.Nested(AddressSchema)
    dropoff_address = fields.fields.Nested(AddressSchema)
    rider = fields.fields.Nested(UserSchema, exclude=('uuid', 'address', 'password', 'email', 'dob', 'roles', 'comments'), dump_only=True)
    assigned_users = fields.fields.Nested(UserSchema, exclude=('address', 'password', 'email', 'dob', 'roles', 'comments'), many=True)
    deliverables = fields.fields.Nested(DeliverableSchema, many=True)
    comments = fields.fields.Nested(CommentSchema, dump_only=True, many=True)
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


class SessionSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.Session
        fields = ('uuid', 'user_uuid',
                  'time_created', 'tasks', 'comments',
                   'links', 'task_count', 'last_active',
                  'time_created', 'time_modified', 'tasks_etag')

    tasks = fields.fields.Nested(TaskSchema, dump_only=True, many=True,
                                 exclude=('comments', 'deliverables'))
    comments = fields.fields.Nested(CommentSchema, dump_only=True, many=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('session_detail', session_id='<uuid>'),
        'collection': ma.URLFor('sessions_list')
    })

    @pre_dump
    def get_last_active(self, data):
        session = get_object(models.Objects.SESSION, data.uuid)
        tasks_plus_deleted = session.tasks.all()
        last_changed_task = sorted(tasks_plus_deleted, key=lambda t: t.time_modified)
        data.last_active = last_changed_task[-1].time_modified if last_changed_task else session.time_modified
        return data

    @pre_dump
    def calculate_tasks_etag(self, data):
        data.tasks_etag = calculate_tasks_etag(data.tasks.all())
        return data

class LocationSchema(ma.ModelSchema, TimesMixin, DeleteFilterMixin):
    class Meta:
        model = models.Location
        fields = ('uuid', 'name', 'contact_name', 'contact_number', 'address', 'comments', 'links',
                  "time_created", "time_modified")

    comments = fields.fields.Nested(CommentSchema, dump_only=True, many=True)
    address = fields.fields.Nested(AddressSchema)

    links = ma.Hyperlinks({
        'self': ma.URLFor('location_detail', location_id='<uuid>'),
        'collection': ma.URLFor('location_list')
    })


class SearchSchema(ma.ModelSchema):
    class Meta:
        fields = ('query', 'type', 'page')
