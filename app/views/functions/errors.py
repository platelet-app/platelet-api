import sys
import traceback

def internalError(message, id = "null"):
    return {'id': id, 'message': str(message)}, 500

def databaseError(id = "null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': id, 'message': "a database error has occurred"}, 500


def notUniqueError(field, id = "null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403


def unauthorisedError(message):
    return {'message': str(message)}, 401


def forbiddenError(message):
    return {'message': str(message)}, 403


def notFound(what, id = "null"):
    return {'id': id, 'message': "The {} was not found".format(str(what))}, 404

