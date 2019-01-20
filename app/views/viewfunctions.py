import sys
import traceback
import functools
from flask_praetorian import utilities
from flask import request
import json


def notFound(id = "null"):
    return {'id': id, 'message': "The user was not found"}, 404


def databaseError(id = "null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': id, 'message': "A database error has occurred"}, 500


def notUniqueError(field, id = "null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403

def unauthorisedError(message):
    return {'message': message}, 401

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

def loadRequestIntoObject(schema, objectToLoadInto):
    requestJson = request.get_json()
    if not requestJson:
        return {'errorMessage' : {'message': "No json input data provided"}, 'httpCode': 400}

    parsedSchema = schema.load(requestJson)
    if parsedSchema.errors:
        return {'errorMessage' : json.dumps(parsedSchema.errors), 'httpCode': 400}  # TODO better error formatting

    objectToLoadInto.updateFromDict(**parsedSchema.data)

    return None
