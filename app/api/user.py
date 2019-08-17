from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import schemas, db, models
from app import user_ns as ns
from app import root_ns
from flask_restplus import Resource, reqparse
import flask_praetorian
from app.api.functions.viewfunctions import user_id_match_or_admin, load_request_into_object
from app.api.functions.userfunctions import get_user_object_by_int_id
from app.api.functions.errors import not_found, schema_validation_error, not_unique_error, forbidden_error, internal_error
from app.exceptions import ObjectNotFoundError, SchemaValidationError, InvalidRangeError
from app.utilities import add_item_to_delete_queue, get_object, get_all_objects, get_range
from app import guard
from flask_praetorian import utilities as prae_util

USER = models.Objects.USER

user_dump_schema = schemas.UserSchema(exclude=("password",
                                               "tasks"))
user_schema = schemas.UserSchema()
users_schema = schemas.UserSchema(many=True, exclude=("address",
                                                      "dob",
                                                      "email",
                                                      "notes",
                                                      "password",
                                                      "name",
                                                      "roles",
                                                      "patch",
                                                      "tasks"))
address_schema = schemas.AddressSchema()
user_username_schema = schemas.UserSchema(exclude=("address",
                                                   "dob",
                                                   "email",
                                                   "notes",
                                                   "password",
                                                   "name",
                                                   "roles",
                                                   "patch",
                                                   "links",
                                                   ))
user_address_schema = schemas.UserSchema(exclude=("username",
                                                   "dob",
                                                   "email",
                                                   "notes",
                                                   "password",
                                                   "name",
                                                   "roles",
                                                   "patch",
                                                   "links",
                                                   ))


@root_ns.route(
    '/whoami',
    endpoint='myself')
class Myself(Resource):
    @flask_praetorian.auth_required
    def get(self):
        try:
            user = get_user_object_by_int_id(prae_util.current_user_id())
        except ObjectNotFoundError:
            return not_found(USER, None)
        except:
            raise
        return jsonify(user_dump_schema.dump(user).data)

@ns.route(
    '/<user_id>',
    endpoint='user')
class User(Resource):
    @flask_praetorian.auth_required
    @user_id_match_or_admin
    @ns.doc(params={'user_id': 'ID for the user'})
    def get(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)
        except:
            raise
        return jsonify(user_dump_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def delete(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        return add_item_to_delete_queue(user)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)
        except:
            raise

        load_request_into_object(USER, instance=user)
        db.session.commit()

        return {'uuid': str(user.uuid), 'message': 'User {} updated.'.format(user.username)}, 200



@ns.route(
    's',
    's/<_range>',
    's/<_range>/<order>',
    endpoint='users')
class Users(Resource):
    @flask_praetorian.roles_accepted('admin')
    def get(self, _range=None, order="ascending"):
        try:
            items = get_range(get_all_objects(USER), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return jsonify(users_schema.dump(items).data)

    def post(self):
        try:
            user = load_request_into_object(USER)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        user.password = guard.encrypt_password(user.password)
        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username")

        return {'uuid': str(user.uuid), 'message': 'User {} created'.format(user.username)}, 201



@ns.route('/<user_id>/username')
class UserNameField(Resource):
    @flask_praetorian.auth_required
    def get(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        return jsonify(user_username_schema.dump(user).data)


@ns.route('/<user_id>/address')
class UserAddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        return jsonify(user_address_schema.dump(user).data)

