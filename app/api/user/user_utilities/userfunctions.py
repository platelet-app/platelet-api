import functools
import logging
import os
import random
import string
from time import sleep
from PIL import Image

from flask_praetorian import utilities
from app import models
from app.api.functions.errors import forbidden_error
from app.exceptions import ObjectNotFoundError, InvalidFileUploadError
from app import db, app
from ....cloud.utilities import get_cloud_store


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


def upload_profile_picture(picture_file_path, crop_dimensions, user_id):
    image = Image.open(picture_file_path)
    cropped = image.crop(crop_dimensions)
    cropped.resize((300, 300))

    # save and convert to jpg here
    cropped_filename = os.path.join(os.path.dirname(picture_file_path), "{}_cropped.jpg".format(picture_file_path))
    thumbnail_filename = os.path.join(os.path.dirname(picture_file_path), "{}_thumbnail.jpg".format(picture_file_path))
    cropped.save(cropped_filename)
    cropped.resize((128, 128))
    cropped.save(thumbnail_filename)
    key_name = "{}_{}.jpg".format(os.path.basename(picture_file_path), user_id)
    thumbnail_key_name = "{}_{}_thumbnail.jpg".format(os.path.basename(picture_file_path), user_id)

    store = get_cloud_store(app.config['CLOUD_PROFILE_PICTURE_STORE_NAME'])
    store.upload(cropped_filename, key_name, delete_original=True)
    store.upload(thumbnail_filename, thumbnail_key_name, delete_original=True)
    user = get_user_object(user_id)
    user.profile_picture_key = key_name
    user.profile_picture_thumbnail_key = thumbnail_key_name
    db.session.commit()
    try:
        os.remove(picture_file_path)
    except IOError as e:
        logging.warning("Could not delete file {}. Reason: {}".format(picture_file_path, e))
    return key_name


def get_presigned_profile_picture_url(user_uuid):
    user = get_user_object(user_uuid)

    store = get_cloud_store(bucket_name=app.config['CLOUD_PROFILE_PICTURE_STORE_NAME'])
    return store.get_presigned_url(user.profile_picture_key)
