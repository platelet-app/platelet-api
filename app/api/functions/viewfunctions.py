import functools
from flask_praetorian import utilities
from flask import request
from app import models
from app.exceptions import InvalidRangeError
from app.exceptions import SchemaValidationError
from app.api.functions.errors import forbidden_error
from app import schemas

user_schema = schemas.UserSchema()
vehicle_schema = schemas.VehicleSchema()
task_schema = schemas.TaskSchema()
session_schema = schemas.SessionSchema()

address_schema = schemas.AddressSchema()
user_username_schema = schemas.UserUsernameSchema()
user_address_schema = schemas.UserAddressSchema()
deliverable_schema = schemas.DeliverableSchema()
note_schema = schemas.NoteSchema()


def user_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, user_id):
        if 'admin' in utilities.current_rolenames():
            return func(self, user_id)
        if utilities.current_user_id() == user_id:
            return func(self, user_id)
        else:
            return forbidden_error("Object not owned by user: user id:".format(user_id))
    return wrapper


def load_request_into_object(model_enum):
    request_json = request.get_json()
    if not request_json:
        raise SchemaValidationError("No json input data provided")

    if model_enum is models.Objects.USER:
        return user_schema.load(request_json).data
    if model_enum is models.Objects.SESSION:
        return session_schema.load(request_json).data
    if model_enum is models.Objects.TASK:
        return task_schema.load(request_json).data
    if model_enum is models.Objects.VEHICLE:
        return vehicle_schema.load(request_json).data
    if model_enum is models.Objects.DELIVERABLE:
        return deliverable_schema.load(request_json).data
    if model_enum is models.Objects.NOTE:
        return note_schema.load(request_json).data


def get_all_users():
    return models.User.query.all()


def get_range(items, _range="0-50", order="descending"):

    start = 0
    end = 50

    if _range:
        between = _range.split('-')

        if between[0].isdigit() and between[1].isdigit():
            start = int(between[0])
            end = int(between[1])
        else:
            raise InvalidRangeError("invalid range")

    if start > end:
        raise InvalidRangeError("invalid range")

    if end - start > 1000:
        raise InvalidRangeError("range too large")

    if order == "descending":
        items.reverse()

    for i in items[:]:
        if i.flagged_for_deletion:
            items.remove(i)

    return items[start:end]
