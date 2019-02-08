import sys
import traceback
import functools
from flask_praetorian import utilities
from flask import request
import json
from app import db
from app import models
from app.views.functions.errors import forbidden_error


def user_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        if utilities.current_user_id() == int(_id):
            return func(self, _id)
        else:
            return {"id": _id, "message": "Object not owned by user"}, 401
    return wrapper



def load_request_into_object(schema, objectToLoadInto):
    requestJson = request.get_json()
    if not requestJson:
        raise Exception("No json input data provided")

    parsedSchema = schema.load(requestJson)
    if parsedSchema.errors:
        raise Exception(parsedSchema.errors)

    objectToLoadInto.updateFromDict(**parsedSchema.data)

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
            return forbidden_error("invalid range")

    if start > end:
        return forbidden_error("invalid range")

    if end - start > 1000:
        return forbidden_error("range too large")

    if order == "descending":
        items.reverse()

    for i in items[:]:
        if i.flaggedForDeletion:
            print(i.id)
            items.remove(i)

    return items[start:end]
