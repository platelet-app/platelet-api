import sys
import traceback

def internal_error(message, id ="null"):
    return {'id': id, 'message': str(message)}, 500

def database_error(id ="null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': id, 'message': "a database error has occurred"}, 500


def not_unique_error(field, id ="null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403


def unauthorised_error(message):
    return {'message': str(message)}, 401


def forbidden_error(message):
    return {'message': str(message)}, 403


def not_found(what, id ="null"):
    return {'id': id, 'message': "The {} was not found".format(str(what))}, 404

