import sys
import traceback
import functools
from flask_praetorian import utilities
from flask import request
import json
from app import db
from app import models
from app import userApi as api


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


def getAllUsers():
    return models.User.query.all()


def getUserObject(_id):

    splitNum = len(api.prefix.split('/'))

    if (request.path.split('/')[splitNum] == 'username'):
        return models.User.query.filter_by(username=_id).first()
    else:
        return models.User.query.filter_by(id=_id).first()


