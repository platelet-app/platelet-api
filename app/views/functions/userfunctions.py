import sys
import traceback
import functools
from flask_praetorian import utilities
from flask import request
import json
from app import db
from app import models
from app import userApi as api


def get_all_users():
    return models.User.query.all()


def get_user_object(_id):

    splitNum = len(api.prefix.split('/'))

    if (request.path.split('/')[splitNum] == 'username'):
        return models.User.query.filter_by(username=_id).first()
    else:
        return models.User.query.filter_by(id=_id).first()


