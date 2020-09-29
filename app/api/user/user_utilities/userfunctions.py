import functools
import os
import random
import string

from flask_praetorian import utilities
from app import models
from app.api.functions.errors import forbidden_error
from app.exceptions import ObjectNotFoundError
from ....cloud import AwsStore

def get_random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

def user_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, user_id):
        if 'admin' in utilities.current_rolenames():
            return func(self, user_id)
        user_int_id = models.User.query.filter_by(uuid=user_id).first().id
        if utilities.current_user_id() == user_int_id:
            return func(self, user_id)
        else:
            print(user_id)
            return forbidden_error("Object not owned by user: user id: {}".format(user_id))

    return wrapper


def get_all_users(filter_deleted=True):
    if filter_deleted:
        return models.User.query.filter_by(flagged_for_deletion=False)
    else:
        return models.User.query.all()


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


def upload_profile_picture(profile_picture):
    file_name = get_random_string(30)
    save_path = os.path.join(os.environ['PROFILE_UPLOAD_FOLDER'], file_name)
    profile_picture.save(save_path)
    if os.environ['CLOUD_PLATFORM'] == "aws":
        store = AwsStore()
        store.upload(save_path, file_name)
    else:
        raise EnvironmentError("Cloud type not specified or not supported.")

    return file_name


def get_presigned_profile_picture_url(user_uuid):
    user = get_user_object(user_uuid)
    if os.environ['CLOUD_PLATFORM'] == "aws":
        store = AwsStore()
        return store.get_presigned_url(user.profile_picture_key)
