import sys
import traceback
import functools
from flask_praetorian import utilities
from flask import request
import json
from app import db
from app import models
from app import userApi as api
from app.exceptions import ObjectNotFoundError


def get_all_users():
    return models.User.query.all()


def get_user_object(_id):

    splitNum = len(api.prefix.split('/'))

    if (request.path.split('/')[splitNum] == 'username'):
        user = models.User.query.filter_by(username=_id).first()
    else:
        user = models.User.query.filter_by(id=_id).first()

    if user:
        return user
    else:
        raise ObjectNotFoundError("User object not found")


def is_user_present(_username):
    if models.User.query.filter_by(username=_username).first():
        return True
    return False
