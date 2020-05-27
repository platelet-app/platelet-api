from marshmallow import ValidationError, pre_dump, post_dump, post_load, EXCLUDE, fields, validates
from app.exceptions import ObjectNotFoundError
from marshmallow_sqlalchemy import field_for
from app import models, ma, flask_version
import datetime
from app.utilities import get_object, calculate_tasks_etag


class TimesMixin:
    time_created = ma.DateTime()
    time_modified = ma.DateTime(dump_only=True)


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


class PostLoadMixin:
    @post_load
    def load_into_object(self, data, many, partial):
        if self.instance:
            for key, value in data.items():
                setattr(self.instance, key, value)
            return self.instance
        else:
            return self.Meta.model(**data)


class ServerSettingsSchema(ma.SQLAlchemySchema, TimesMixin, PostLoadMixin):
    class Meta:
        model = models.ServerSettings
        fields = ('organisation_name', 'image_url',
                  'version', 'hostname', 'favicon', 'locale',
                  'locale_id')

    locale = ma.Nested('LocaleSchema', dump_only=True, exclude=('id',))

    @post_dump()
    def flask_version(self, data, many):
        data['flask_version'] = flask_version
        return data


class LocaleSchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        model = models.Locale
        fields = ('label', 'id', 'code')


class CommentSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Comment
        fields = ('uuid', 'body', 'author', 'parent_uuid', 'author_uuid',
                  "time_created", "time_modified", "publicly_visible")
    author = ma.Nested(
        'UserSchema', dump_only=True,
        exclude=('username', 'address', 'password', 'name', 'email',
                 'dob', 'patch', 'roles', 'comments', 'assigned_vehicles', 'patch_id',
                 "time_created", "time_modified"))


class DeliverableTypeSchema(ma.SQLAlchemySchema, TimesMixin, PostLoadMixin):
    class Meta:
        model = models.DeliverableType
        fields = ('id', 'label')


class DeliverableSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Deliverable
        fields = ('uuid', 'task_uuid', 'comments', 'type', 'type_id',
                  "time_created", "time_modified")

    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    type = fields.Pluck(DeliverableTypeSchema, "label", dump_only=True)


class AddressSchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        model = models.Address

        fields = ('ward', 'line1', 'line2', 'town',
                  'county', 'country', 'postcode',
                  'what3words')

    #postcode = ma.Function(lambda obj: obj.postcode.upper())


class PatchSchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        model = models.Patch
        fields = ('id', 'label')


class UserSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.User
        fields = ('uuid', 'username', 'address', 'password', 'name', 'email',
                  'dob', 'patch', 'roles', 'comments', 'display_name',
                  'assigned_vehicles', 'patch_id', 'contact_number',
                  'time_created', 'time_modified', 'links')

    username = ma.Str(required=True)
    email = ma.Email()
    dob = ma.DateTime(format='%d/%m/%Y')
    address = ma.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    assigned_vehicles = ma.Nested("VehicleSchema", many=True, dump_only=True, exclude=("assigned_user",))
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    #tasks = ma.Nested(TaskSchema, many=True)

    links = ma.Hyperlinks(
        {"self": ma.URLFor("user", user_id="<uuid>"), "collection": ma.URLFor("users")}
    )

    patch = fields.Pluck(PatchSchema, "label", dump_only=True)


class VehicleSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Vehicle
        fields = ('uuid', 'manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'comments', 'links', 'name', 'assigned_user', 'assigned_user_uuid',
                  "time_created", "time_modified")

    date_of_manufacture = ma.DateTime(format='%d/%m/%Y')
    date_of_registration = ma.DateTime(format='%d/%m/%Y')
    assigned_user = ma.Nested(UserSchema, dump_only=True)
    assigned_user_uuid = ma.String(allow_none=True)
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    uuid = ma.String(dump_only=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', vehicle_id='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    }, dump_only=True)

    @validates("date_of_registration")
    def validate_date_of_registration(self, value):
        try:
            datetime.datetime.strptime(value, '%d/%m/%Y')
        except ValueError:
            raise ValidationError("{} has invalid date format, should be %d/%m/%Y".format(value))

        if self.date_of_manufacture and self.date_of_manufacture > value:
            raise ValidationError("date of registration cannot be before date of manufacture")


class PrioritySchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        model = models.Priority
        fields = ('id', 'label')


class TaskSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Task
        fields = ('uuid', 'pickup_address', 'dropoff_address', 'patch', 'patch_id', 'contact_name',
                  'contact_number', 'priority', 'session_uuid', 'time_of_call', 'deliverables',
                  'comments', 'links', 'assigned_rider', 'time_picked_up', 'time_dropped_off', 'rider',
                  'priority_id', 'time_cancelled', 'time_rejected', "patient_name", "patient_contact_number",
                  "destination_contact_number", "destination_contact_name",
                  "time_created", "time_modified", "assigned_users")

    pickup_address = ma.Nested(AddressSchema)
    dropoff_address = ma.Nested(AddressSchema)
    rider = ma.Nested(UserSchema, exclude=('uuid', 'address', 'password', 'email', 'dob', 'roles', 'comments'), dump_only=True)
    assigned_users = ma.Nested(UserSchema, exclude=('address', 'password', 'email', 'dob', 'roles', 'comments'), many=True)
    deliverables = ma.Nested(DeliverableSchema, many=True)
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    pickup_time = ma.DateTime(allow_none=True)
    time_dropped_off = ma.DateTime(allow_none=True)
    time_cancelled = ma.DateTime(allow_none=True)
    time_rejected = ma.DateTime(allow_none=True)
    priority = fields.Pluck(PrioritySchema, "label", dump_only=True)
    patch = fields.Pluck(PatchSchema, "label", dump_only=True)
    time_of_call = ma.DateTime()

    links = ma.Hyperlinks({
        'self': ma.URLFor('task_detail', task_id='<uuid>'),
        'collection': ma.URLFor('tasks_list')
    })


class UserUsernameSchema(ma.SQLAlchemySchema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username')

    username = ma.Str(required=True)


class UserAddressSchema(ma.SQLAlchemySchema):
    class Meta:
        model = models.User
        fields = ('uuid', 'name', 'address')

    postcode = ma.Function(lambda obj: obj.postcode.upper())
    address = ma.Nested(AddressSchema, exclude=("ward",))


class SessionSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Session
        fields = ('uuid', 'user_uuid',
                  'time_created', 'tasks', 'comments',
                   'links', 'task_count', 'last_active',
                  'time_created', 'time_modified', 'tasks_etag')

    tasks = ma.Nested(TaskSchema, dump_only=True, many=True,
                                 exclude=('comments', 'deliverables'))
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('session_detail', session_id='<uuid>'),
        'collection': ma.URLFor('sessions_list')
    })

    @pre_dump(pass_many=False)
    def get_last_active(self, data, many):
        session = get_object(models.Objects.SESSION, data.uuid)
        tasks_plus_deleted = session.tasks.all()
        last_changed_task = sorted(tasks_plus_deleted, key=lambda t: t.time_modified)
        data.last_active = last_changed_task[-1].time_modified if last_changed_task else session.time_modified
        return data

    @pre_dump(pass_many=False)
    def get_tasks_etag(self, data, many):
        data.tasks_etag = calculate_tasks_etag(data.tasks.all())
        return data


class LocationSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        model = models.Location
        fields = ('uuid', 'name', 'contact_name', 'contact_number', 'address', 'comments', 'links',
                  "time_created", "time_modified")

    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    address = ma.Nested(AddressSchema)

    links = ma.Hyperlinks({
        'self': ma.URLFor('location_detail', location_id='<uuid>'),
        'collection': ma.URLFor('location_list')
    })


class SearchSchema():
    class Meta:
        fields = ('query', 'type', 'page')
