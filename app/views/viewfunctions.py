import sys
import traceback
import functools
from flask_praetorian import utilities

def notFound(id = "null"):
    return {'id': id, 'message': "The user was not found"}, 404


def databaseError(id = "null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': id, 'message': "A database error has occurred"}, 500


def notUniqueError(field, id = "null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403

def userIdMatchOrAdmin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        if utilities.current_user_id() == int(_id):
            return func(self, _id)
        else:
            return {"id": _id, "message": "Object not owned by user"}, 401
    return wrapper
