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

def get_range(item, _range="0-50", order="descending"):

    start = 0
    end = 50

    if _range:
        between = _range.split('-')

        if between[0].isdigit() and between[1].isdigit():
            start = int(between[0])
            end = int(between[1])
        else:
            return forbiddenError("invalid range")

    if start > end:
        return forbiddenError("invalid range")

    if end - start > 1000:
        return forbiddenError("range too large")

    if order == "descending":
        item.reverse()

    return item[start:end]

