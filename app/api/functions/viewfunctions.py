import functools
from flask_praetorian import utilities
from flask import request
from app import models
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
location_schema = schemas.LocationSchema()


def user_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, user_id):
        if 'admin' in utilities.current_rolenames():
            return func(self, user_id)
        user_int_id = models.User.query.filter_by(uuid=user_id).first().id
        if utilities.current_user_id() == user_int_id:
            return func(self, user_id)
        else:
            print(user_id)
            return forbidden_error("Object not owned by user: user id: {}".format(user_id))
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
    if model_enum is models.Objects.LOCATION:
        return location_schema.load(request_json).data


