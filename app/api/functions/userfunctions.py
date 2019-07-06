from app import models
from app.exceptions import ObjectNotFoundError


def get_all_users():
    users = models.User.query.all()
    if not users:
        return {}
    return users


def get_user_object(user_id):
    user = models.User.query.filter_by(uuid=user_id).first()

    if not user:
        raise ObjectNotFoundError()

    return user

def get_user_object_by_int_id(user_id):
    user = models.User.query.filter_by(id=user_id).first()

    if not user:
        raise ObjectNotFoundError()

    return user

def is_username_present(username):
    if models.User.query.filter_by(username=username).first():
        return True
    return False


def is_user_present(id):
    if models.User.query.filter_by(uuid=id).first():
        return True
    return False
