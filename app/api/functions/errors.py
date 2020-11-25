import sys
import traceback
import app.api.functions.utilities as utilities


def internal_error(message, object_id="null"):
    return {'id': object_id, 'message': str(message)}, 500


def schema_validation_error(message):
    return {'message': "Invalid input: {}".format(str(message))}, 400


def unprocessable_entity_error(message, object_id="null"):
    return {'message': "Unprocessable entity: {}".format(str(message))}, 422


def database_error(object_id="null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': object_id, 'message': "a database error has occurred"}, 500


def not_unique_error(field, object_id="null"):
    return {'id': object_id, 'message': "{} not unique".format(field)}, 403


def unauthorised_error(message):
    return {'message': str(message)}, 401


def forbidden_error(message, object_id=None):
    if object_id:
        return {'id': object_id, 'message': str(message)}, 403
    return {'message': str(message)}, 403


def already_flagged_for_deletion_error(object_type, object_id):
    return forbidden_error("{} already flagged for deletion".format(utilities.object_type_to_string(object_type)),
                           object_id)


def not_found(object_type, object_id="null"):
    return {'id': object_id, 'message': "{} not found".format(utilities.object_type_to_string(object_type))}, 404
