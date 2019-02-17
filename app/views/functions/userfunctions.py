from flask import request
from app import models
from app import userApi as api
from app.exceptions import ObjectNotFoundError


def get_all_users():
    return models.User.query.all()


def get_user_object(_id):

    split_num = len(api.prefix.split('/'))

    if request.path.split('/')[split_num] == 'username':
        user = models.User.query.filter_by(username=_id).first()
    else:
        user = models.User.query.filter_by(id=_id).first()

    if user:
        return user
    else:
        raise ObjectNotFoundError("User object not found")


def is_username_present(username):
    if models.User.query.filter_by(username=username).first():
        return True
    return False


def is_user_present(id):
    if models.User.query.filter_by(id=id).first():
        return True
    return False
