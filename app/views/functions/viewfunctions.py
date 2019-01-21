import sys
import traceback
import functools
from flask_praetorian import utilities
from flask import request
import json
from app import db
from app import models


def databaseError(id = "null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': id, 'message': "a database error has occurred"}, 500


def notUniqueError(field, id = "null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403


def unauthorisedError(message):
    return {'message': message}, 401


def forbiddenError(message):
    return {'message': message}, 403


def notFound(what, id = "null"):
    return {'id': id, 'message': "The {} was not found".format(what)}, 404


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

def getAllUsers():
    return models.User.query.all()
