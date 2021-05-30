import imghdr
import logging
import os
import base64

from flask import jsonify, request
from marshmallow import ValidationError
from werkzeug.datastructures import FileStorage

from app import schemas, db, models, redis_queue, app
from app import user_ns as ns
from app import root_ns
from flask_restx import Resource, reqparse
import flask_praetorian
from app.api.functions.viewfunctions import load_request_into_object
from app.api.user.user_utilities.userfunctions import user_id_match_or_admin, \
    upload_profile_picture, get_presigned_profile_picture_url, get_random_string
from app.api.functions.errors import not_found, schema_validation_error, forbidden_error, \
    internal_error, already_flagged_for_deletion_error
from app.exceptions import ObjectNotFoundError, InvalidRangeError, AlreadyFlaggedForDeletionError
from app.api.functions.utilities import add_item_to_delete_queue, get_object, \
    remove_item_from_delete_queue, get_page, get_query
from app import guard
from flask_praetorian import utilities as prae_util

USER = models.Objects.USER
DELETE_FLAG = models.Objects.DELETE_FLAG

user_dump_schema = schemas.UserSchema(exclude=("password", "comments"))
user_schema = schemas.UserSchema()
users_schema = schemas.UserSchema(
    exclude=("address",
             "dob",
             "email",
             "password",
             "comments"))
address_schema = schemas.AddressSchema()
user_username_schema = schemas.UserSchema(exclude=("address",
                                                   "dob",
                                                   "email",
                                                   "password",
                                                   "name",
                                                   "roles",
                                                   "patch",
                                                   "links",
                                                   ))
user_address_schema = schemas.UserSchema(exclude=("username",
                                                  "dob",
                                                  "email",
                                                  "password",
                                                  "name",
                                                  "roles",
                                                  "patch",
                                                  "links",
                                                  ))
tasks_schema = schemas.TaskSchema(many=True)

upload_parser = ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)


@root_ns.route(
    '/whoami',
    endpoint='myself')
class Myself(Resource):
    @flask_praetorian.auth_required
    def get(self):
        jwt_details = flask_praetorian.utilities.get_jwt_data_from_app_context()
        try:
            user = prae_util.current_user()
        except ObjectNotFoundError:
            return not_found(USER, None)
        result = user_dump_schema.dump(user)
        result['login_expiry'] = None
        result['refresh_expiry'] = None
        if jwt_details:
            try:
                result['login_expiry'] = int(jwt_details['rf_exp']) * 1000
                result['refresh_expiry'] = int(jwt_details['exp']) * 1000
            except ValueError:
                logging.warning("The expiry is not an int for some reason.")
            except KeyError as e:
                logging.warning("Could not find login or refresh expiry data:".format(str(e)))

        return jsonify(result)


@ns.route('/<user_id>/restore', endpoint="user_undelete")
class UserRestore(Resource):
    @flask_praetorian.roles_accepted("admin", "coordinator")
    def put(self, user_id):
        try:
            user = get_object(USER, user_id, with_deleted=True)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        if user.deleted:
            remove_item_from_delete_queue(user)
        else:
            return {'uuid': str(user.uuid), 'message': 'User {} not flagged for deletion.'.format(user.uuid)}, 200
        return {'uuid': str(user.uuid), 'message': 'User {} deletion flag removed.'.format(user.uuid)}, 200


@ns.route(
    '/<user_id>',
    endpoint='user',
    doc={'params': {'user_id': 'UUID for the user'}}
)
class User(Resource):
    @flask_praetorian.auth_required
    def get(self, user_id):
        # we know this is going to return profile picture urls so initialise the store here
        from app import cloud_stores
        cloud_stores.initialise_profile_pictures_store()
        try:
            return jsonify(user_dump_schema.dump(get_object(USER, user_id)))
        except ObjectNotFoundError:
            return not_found(USER, user_id)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def delete(self, user_id):
        if str(prae_util.current_user().uuid) == user_id:
            return forbidden_error("You can't delete yourself.", user_id)
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)
        if "admin" in user.roles:
            return forbidden_error(
                "You cannot delete an admin user. If you'd like to delete this user the admin role must be removed first.",
                user_id
            )
        try:
            add_item_to_delete_queue(user)
        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(USER, str(user.uuid))

        return {'uuid': str(user.uuid), 'message': "User deleted"}, 202

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def patch(self, user_id):
        try:
            user = get_object(USER, user_id)
            if user.deleted:
                return not_found(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        try:
            new_user = load_request_into_object(USER, instance=user)
        except ValidationError as e:
            return schema_validation_error(e)
        # TODO: check this is right, might always be password field?
        if new_user.password:
            new_user.password = guard.encrypt_password(new_user.password)
            if new_user.password_reset_on_login:
                new_user.password_reset_on_login = False

        db.session.commit()

        return {'uuid': str(user.uuid), 'message': 'User {} updated.'.format(user.username)}, 200


@ns.route(
    's',
    endpoint='users')
class Users(Resource):
    @flask_praetorian.auth_required
    def get(self):
        # we know this is going to return profile picture urls so initialise the store here
        from app import cloud_stores
        cloud_stores.initialise_profile_pictures_store()
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("page", type=int, location="args")
            parser.add_argument("order", type=str, location="args")
            parser.add_argument("role", type=str, location="args")
            args = parser.parse_args()
            page = args['page'] if args['page'] else 1
            order = args['order'] if args['order'] else "newest"
            role = args['role']
            items = get_page(get_query(USER, filter_deleted=True), page, model=models.User, order=order)
            if role:
                items = filter(lambda u: role in u.roles.split(","), items)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return users_schema.dump(items, many=True)

    @flask_praetorian.roles_accepted('admin')
    def post(self):
        try:
            user = load_request_into_object(USER)
        except ValidationError as e:
            return schema_validation_error(str(e))

        user.password = guard.hash_password(user.password if user.password else "")

        db.session.add(user)
        db.session.commit()
        return {'uuid': str(user.uuid), 'message': 'User {} created'.format(user.username)}, 201


@ns.route('/<user_id>/profile_picture')
class UserProfilePicture(Resource):
    @flask_praetorian.auth_required
    def get(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("size", type=int, location="args")
        return {'uuid': str(user_id), 'user_profile_picture_url': get_presigned_profile_picture_url(user_id)}, 200

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def post(self, user_id):
        try:
            uploaded_file = request.files['file']
        except KeyError:
            return forbidden_error("A image file must be provided.")
        try:
            crop_dimensions = request.form['crop_dimensions']
        except KeyError:
            return forbidden_error("Crop dimensions must be provided.")
        crop_dimensions_list = crop_dimensions.split(",")
        for i, dim in enumerate(crop_dimensions_list):
            try:
                crop_dimensions_list[i] = int(dim)
            except ValueError:
                return schema_validation_error("Crop dimensions must be integers.")


        file_name = get_random_string(30)
        save_path = os.path.join(app.config['PROFILE_PROCESSING_DIRECTORY'], file_name)
        uploaded_file.save(save_path)

        # Validate it is an actual image
        image_types = ["jpg", "gif", "png"]
        if not imghdr.what(save_path) in image_types:
            return forbidden_error("Profile picture uploads must be either a jpg, gif or png")

        # Put it into the queue for cropping, resizing and uploading
        crop_dimensions_tuple = tuple(crop_dimensions_list)
        job = redis_queue.enqueue_call(
            func=upload_profile_picture,
            args=(save_path, user_id),
            kwargs=({"crop_dimensions": crop_dimensions_tuple}),
            result_ttl=5000
        )
        return {'uuid': str(user_id), 'message': 'Profile picture uploaded and is processing.', 'job_id': job.get_id()}, 201

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("image_data")
        args = parser.parse_args()

        file_name = get_random_string(30)
        save_path = os.path.join(app.config['PROFILE_PROCESSING_DIRECTORY'], file_name)
        with open(save_path, "wb") as fh:
            fh.write(base64.decodebytes(bytes(args['image_data'], 'utf-8')))

        # Validate it is an actual image
        image_types = ["jpeg", "gif", "png"]
        if not imghdr.what(save_path) in image_types:
            return forbidden_error("Profile picture uploads must be either a jpg, gif or png")

        # Put it into the queue for cropping, resizing and uploading
       # upload_profile_picture(save_path, user_id)
        job = redis_queue.enqueue_call(
            # TODO: ttl config
            func=upload_profile_picture, args=(save_path, user_id), result_ttl=50000
        )
        return {'uuid': str(user_id), 'message': 'Profile picture uploaded and is processing.', 'job_id': job.get_id()}, 201

