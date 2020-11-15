import functools
from flask import request
from app import models
from app.exceptions import SchemaValidationError
from app.api.functions.errors import forbidden_error
from app import schemas
from app import logger

user_schema = schemas.UserSchema()
vehicle_schema = schemas.VehicleSchema()
task_schema = schemas.TaskSchema()
address_schema = schemas.AddressSchema()
user_username_schema = schemas.UserUsernameSchema()
user_address_schema = schemas.UserAddressSchema()
deliverable_schema = schemas.DeliverableSchema()
comment_schema = schemas.CommentSchema()
location_schema = schemas.LocationSchema()


def load_request_into_object(model_enum, instance=None, partial=True):
    request_json = request.get_json()
    if not request_json:
        logger.warning("No json input data provided")

    if model_enum is models.Objects.USER:
        return user_schema.load(request_json, instance=instance if instance else None, partial=partial)
    if model_enum is models.Objects.TASK:
        return task_schema.load(request_json, instance=instance if instance else None, partial=partial)
    if model_enum is models.Objects.VEHICLE:
        return vehicle_schema.load(request_json, instance=instance if instance else None, partial=partial)
    if model_enum is models.Objects.DELIVERABLE:
        return deliverable_schema.load(request_json, instance=instance if instance else None, partial=partial)
    if model_enum is models.Objects.COMMENT:
        return comment_schema.load(request_json, instance=instance if instance else None, partial=partial)
    if model_enum is models.Objects.LOCATION:
        return location_schema.load(request_json, instance=instance if instance else None, partial=partial)


def load_request_into_dict(model_enum):
    request_json = request.get_json()
    if not request_json:
        raise SchemaValidationError("No json input data provided")

    if model_enum is models.Objects.USER:
        return user_schema.load(request_json)
    if model_enum is models.Objects.TASK:
        return task_schema.load(request_json)
    if model_enum is models.Objects.VEHICLE:
        return vehicle_schema.load(request_json)
    if model_enum is models.Objects.DELIVERABLE:
        return deliverable_schema.load(request_json)
    if model_enum is models.Objects.COMMENT:
        return comment_schema.load(request_json)
    if model_enum is models.Objects.LOCATION:
        return location_schema.load(request_json)

