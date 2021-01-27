import copy
import json
from functools import reduce

import phonenumbers
from marshmallow import ValidationError, pre_dump, post_dump, post_load, EXCLUDE, fields, validates
from phonenumbers import NumberParseException

from app import cloud_stores
from app.api.task.task_utilities.taskfunctions import calculate_task_etag
from app.exceptions import ObjectNotFoundError
from marshmallow_sqlalchemy import field_for
from app import models, ma, app
from app.api.functions.utilities import get_all_objects, object_type_to_string


class TimesMixin:
    time_created = ma.DateTime(dump_only=True)
    time_modified = ma.DateTime(dump_only=True)


class DeleteFilterMixin:
    @pre_dump(pass_many=True)
    def filter_deleted(self, data, many):
        if many:
            return list(filter(lambda t: not t.deleted, data))
        else:
            if data.deleted:
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


class LocaleSchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        model = models.Locale
        fields = ('label', 'id', 'code')


def comment_edits_only_filter(action):
    if not action.http_request_type or not action.data_fields:
        return False
    return action.http_request_type.label in ["PATCH", "PUT"] and "body" in action.data_fields


def count_comment_edits(comment):
    return len(list(filter(comment_edits_only_filter, comment.logged_actions)))


class CommentSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Comment
        fields = ('uuid', 'body', 'author', 'parent_uuid', 'author_uuid',
                  "time_created", "time_modified", "publicly_visible", "num_edits"
                  )

    author = ma.Nested(
        'UserSchema', dump_only=True,
        only=("display_name", "uuid", "profile_picture_thumbnail_url")
    )
    num_edits = ma.Function(
        count_comment_edits
    )


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

    ward = ma.Str(allow_none=True)
    line1 = ma.Str(allow_none=True)
    line2 = ma.Str(allow_none=True)
    town = ma.Str(allow_none=True)
    county = ma.Str(allow_none=True)
    country = ma.Str(allow_none=True)
    postcode = ma.Str(allow_none=True)
    what3words = ma.Str(allow_none=True)


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
                  'time_created', 'time_modified', 'links', 'password_reset_on_login',
                  'profile_picture_url', 'profile_picture_thumbnail_url')

    username = ma.Str(required=True)
    email = ma.Email(allow_none=True)
    dob = ma.DateTime(format='%d/%m/%Y', allow_none=True)
    address = ma.Nested(AddressSchema)
    uuid = field_for(models.User, 'uuid', dump_only=True)
    assigned_vehicles = ma.Nested("VehicleSchema", many=True, dump_only=True, exclude=("assigned_user",))
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    password = ma.Str(load_only=True)
    password_reset_on_login = ma.Bool(dump_only=True)
    patch_id = ma.Int(allow_none=True)
    profile_picture_url = ma.Str(dump_only=True)
    profile_picture_thumbnail_url = ma.Str(dump_only=True)

    links = ma.Hyperlinks(
        {"self": ma.URLFor("user", user_id="<uuid>"), "collection": ma.URLFor("users")}
    )

    patch = fields.Pluck(PatchSchema, "label", dump_only=True)

    @validates("display_name")
    def check_display_name_unique(self, value):
        # TODO: this trips up even if the user being changed is the same as the one with the display_name
        users = get_all_objects(models.Objects.USER)
        if any(list(filter(lambda u: u.display_name == value, users))):
            raise ValidationError("This display name is already taken.")

    @validates("username")
    # TODO: this trips up even if the user being changed is the same as the one with the username
    def check_username_unique(self, value):
        users = get_all_objects(models.Objects.USER)
        if any(list(filter(lambda u: u.username == value, users))):
            raise ValidationError("This username is already taken.")


    @pre_dump
    def profile_picture_protected_url(self, data, many):
        store = cloud_stores.get_profile_picture_store()
        if not many:
            if data.profile_picture_key and store:
                data.profile_picture_url = store.get_presigned_image_url(data.profile_picture_key)
            else:
                data.profile_picture_url = app.config['DEFAULT_PROFILE_PICTURE_URL']
        return data

    @pre_dump
    def profile_picture_protected_thumbnail_url(self, data, many):
        store = cloud_stores.get_profile_picture_store()
        if data.profile_picture_thumbnail_key and store:
            data.profile_picture_thumbnail_url = store.get_presigned_image_url(data.profile_picture_thumbnail_key)
        else:
            data.profile_picture_thumbnail_url = None

        return data

    @post_dump
    def split_roles(self, data, many):
        try:
            if data['roles']:
                data['roles'] = data['roles'].split(",")
            else:
                data['roles'] = ""
        except KeyError:
            return data
        return data


class VehicleSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Vehicle
        fields = ('uuid', 'manufacturer', 'model', 'date_of_manufacture', 'date_of_registration',
                  'registration_number', 'comments', 'links', 'name', 'assigned_user', 'assigned_user_uuid',
                  "time_created", "time_modified")

    date_of_manufacture = ma.Date(format='%d/%m/%Y')
    date_of_registration = ma.Date(format='%d/%m/%Y')
    assigned_user = ma.Nested(UserSchema, dump_only=True)
    assigned_user_uuid = ma.String(allow_none=True)
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    uuid = ma.String(dump_only=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('vehicle_detail', vehicle_id='<uuid>'),
        'collection': ma.URLFor('vehicle_list')
    }, dump_only=True)


class PrioritySchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        model = models.Priority
        fields = ('id', 'label')


def display_names_reducer(result, user):
    if user[0] == 0:
        return result + user[1].display_name
    else:
        return result + ", {}".format(user[1].display_name)


class ContactSchema(ma.SQLAlchemySchema, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Contact
        fields = ('name', 'address', 'telephone_number', 'mobile_number', 'email_address')

    name = ma.String(allow_none=True)
    address = ma.String(allow_none=True)
    telephone_number = ma.String(allow_none=True)
    mobile_number = ma.String(allow_none=True)
    email_address = ma.String(allow_none=True)

    @validates("telephone_number")
    def telephone_number(self, value):
        validate_tel_number(value)
        return
        # TODO: see if this is a better way to do things
        if not value:
            return
        try:
            phonenumbers.parse(value)
        except NumberParseException:
            raise
            raise ValidationError("Not a valid telephone number.")

  #  @validates("mobile_number")
  #  def mobile_number(self, value):
  #      validate_tel_number(value)


class TasksParentSchema(ma.SQLAlchemySchema):
    class Meta:
        unknown = EXCLUDE
        model = models.TasksParent

        fields = ('relays', 'reference')

    relays = ma.Nested('TaskSchema', many=True, dump_only=True)
    reference = ma.String(dump_only=True)


class TaskSchema(ma.SQLAlchemySchema, TimesMixin, PostLoadMixin):
    class Meta:
        unknown = EXCLUDE
        model = models.Task
        fields = ('uuid', 'pickup_address', 'dropoff_address', 'patch', 'patch_id', 'requester_contact',
                  'priority', 'time_of_call', 'deliverables',
                  'comments', 'links', 'time_picked_up', 'time_dropped_off', 'rider',
                  'priority_id', 'time_cancelled', 'time_rejected',
                  'time_created', 'time_modified', 'assigned_coordinators', 'assigned_riders',
                  'assigned_riders_display_string', 'assigned_coordinators_display_string', 'author',
                  'relay_previous_uuid', 'relay_next', 'relay_previous', 'parent_id', 'order_in_relay',
                  'etag', 'reference', 'saved_location_pickup', 'saved_location_dropoff')

    requester_contact = ma.Nested(ContactSchema, allow_none=True)

    saved_location_pickup = ma.Nested("LocationSchema")
    saved_location_dropoff = ma.Nested("LocationSchema")

    pickup_address = ma.Nested(AddressSchema, allow_none=True)
    dropoff_address = ma.Nested(AddressSchema, allow_none=True)
    assigned_riders = ma.Nested(UserSchema,
                                only=('uuid', 'display_name', 'patch', 'profile_picture_thumbnail_url'),
                                many=True, dump_only=True)
    assigned_coordinators = ma.Nested(UserSchema,
                                      only=('uuid', 'display_name', 'profile_picture_thumbnail_url'),
                                      many=True, dump_only=True)
    author = ma.Nested(UserSchema, only=('uuid', 'display_name'), dump_only=True)
    deliverables = ma.Nested(DeliverableSchema, many=True)
    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    time_picked_up = ma.DateTime(allow_none=True)
    time_dropped_off = ma.DateTime(allow_none=True)
    time_cancelled = ma.DateTime(allow_none=True)
    time_rejected = ma.DateTime(allow_none=True)
    priority = fields.Pluck(PrioritySchema, "label", dump_only=True)
    priority_id = ma.Int(allow_none=True)
    patch = fields.Pluck(PatchSchema, "label", dump_only=True)
    patch_id = ma.Int(allow_none=True)
    time_of_call = ma.DateTime()
    assigned_users_display_string = ma.String(dump_only=True)
    relay_previous = ma.Nested('self', only=('uuid',), dump_only=True)
    relay_next = ma.Nested('self', only=('uuid',), dump_only=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('task_detail', task_id='<uuid>'),
        'collection': ma.URLFor('tasks_list_all')
    })

    @pre_dump
    def concatenate_assigned_riders_display_string(self, data, many):
        data.assigned_riders_display_string = reduce(display_names_reducer, enumerate(data.assigned_riders), "")
        return data

    @pre_dump
    def concatenate_assigned_coordinators_display_string(self, data, many):
        data.assigned_coordinators_display_string = reduce(
            display_names_reducer,
            enumerate(data.assigned_coordinators), "")
        return data

    @post_dump
    def calculate_etag(self, data, many):
        copied_data = copy.deepcopy(data)
        # TODO: slightly annoying workaround to avoid new cloud urls changing the etag, dunno if it can be done better
        try:
            for i in copied_data['assigned_coordinators']:
                del i['profile_picture_thumbnail_url']
        except KeyError:
            pass
        try:
            for i in copied_data['assigned_riders']:
                del i['profile_picture_thumbnail_url']
        except KeyError:
            pass
        try:
            del copied_data['comments']
        except KeyError:
            pass
        data['etag'] = calculate_task_etag(json.dumps(copied_data))
        return data


def validate_tel_number(value):
    if not value:
        return
    split_list = list(value)
    if len(list((filter(lambda n: n == "+", split_list)))) > 1:
        raise ValidationError("Not a valid telephone number.")
    if "+" in split_list and split_list[0] != "+":
        raise ValidationError("Not a valid telephone number.")
    if any(list(filter(int_check, split_list))):
        raise ValidationError("Not a valid telephone number.")


def int_check(value):
    if value == "+" or value == " ":
        return False
    try:
        int(value)
    except ValueError:
        return True
    return False


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


class LocationSchema(ma.SQLAlchemySchema, TimesMixin, DeleteFilterMixin, PostLoadMixin):
    class Meta:
        model = models.Location
        fields = ('uuid', 'name', 'contact', 'address', 'comments', 'links',
                  "time_created", "time_modified")

    comments = ma.Nested(CommentSchema, dump_only=True, many=True)
    address = ma.Nested(AddressSchema)
    contact = ma.Nested(ContactSchema, allow_none=True)

    links = ma.Hyperlinks({
        'self': ma.URLFor('location_detail', location_id='<uuid>'),
        'collection': ma.URLFor('location_list')
    })


class HTTPRequestTypeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = models.HTTPRequestType
        fields = ('label',)

    label = ma.String(dump_only=True)


class HTTPResponseStatusSchema(ma.SQLAlchemySchema):
    class Meta:
        model = models.HTTPResponseStatus
        fields = ('status', 'status_description', 'status_type')

    status = ma.Integer(dump_only=True)
    status_description = ma.String(dump_only=True)
    status_type = ma.String(dump_only=True)


class LogEntrySchema(ma.SQLAlchemySchema):
    class Meta:
        model = models.LogEntry
        fields = ('uuid', 'time_created', 'parent_uuid', 'calling_user',
                  'http_request_type', 'http_response_status', 'parent_type',
                  'data_fields')

    time_created = ma.DateTime(dump_only=True)
    parent_uuid = ma.String(dump_only=True)
    http_request_type = ma.Pluck(HTTPRequestTypeSchema, "label", dump_only=True)
    http_response_status = ma.Nested(HTTPResponseStatusSchema, dump_only=True)
    parent_type = ma.Function(lambda obj: object_type_to_string(obj.parent_type))

    calling_user = ma.Nested(UserSchema, dump_only=True, only=("uuid", "display_name"))


class SearchSchema():
    class Meta:
        fields = ('query', 'type', 'page')
