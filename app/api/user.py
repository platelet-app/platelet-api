from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import schemas, db, models
from app import user_ns as ns
from flask_restplus import Resource, reqparse
import flask_praetorian
from app.api.functions.viewfunctions import user_id_match_or_admin, load_request_into_object
from app.api.functions.errors import not_found, schema_validation_error, not_unique_error
from app.exceptions import ObjectNotFoundError, SchemaValidationError
from app.utilities import add_item_to_delete_queue, get_object, get_all_objects
from app import guard

USER = models.Objects.USER

user_dump_schema = schemas.UserSchema(exclude=("password",))
user_schema = schemas.UserSchema()
users_schema = schemas.UserSchema(many=True, exclude=('address',
                                                      'dob',
                                                      'email',
                                                      'notes',
                                                      'password',
                                                      'name',
                                                      'roles',
                                                      'patch'))
address_schema = schemas.AddressSchema()
user_username_schema = schemas.UserSchema(exclude=('address',
                                                   'dob',
                                                   'email',
                                                   'notes',
                                                   'password',
                                                   'name',
                                                   'roles',
                                                   'patch',
                                                   'links',
                                                   ))
user_address_schema = schemas.UserSchema(exclude=('username',
                                                   'dob',
                                                   'email',
                                                   'notes',
                                                   'password',
                                                   'name',
                                                   'roles',
                                                   'patch',
                                                   'links',
                                                   ))


@ns.route(
    '/<user_id>',
    endpoint='user')
class User(Resource):
    @flask_praetorian.auth_required
    @user_id_match_or_admin
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

        new_data = load_request_into_object(USER)
        # load_request_into_dict function to use here?
        # might just do that anyway with incomplete data
        models.User.query.filter_by(uuid=user_id).update(new_data)
        db.session.commit()

        return {'uuid': str(user.uuid), 'message': 'User {} updated.'.format(user.username)}, 200

        #print(user_dump_schema.dump(new_data).data



@ns.route(
    's',
    endpoint='users')
class Users(Resource):
    @flask_praetorian.roles_accepted('admin')
    def get(self):
        #TODO: Any need to restrict this to a range?
        users = get_all_objects(USER)

        return jsonify(users_schema.dump(users).data)

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

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, user_id):

        parser = reqparse.RequestParser()
        parser.add_argument('username')
        args = parser.parse_args()
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        if args['username']:
            user.username = args['username']

        else:
            return schema_validation_error("No data")

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username", str(user.uuid))

        return {'uuid': str(user.uuid), 'message': 'User {} updated'.format(user.username)}, 200



@ns.route('/<user_id>/address')
class UserAddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        return jsonify(user_address_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, user_id):
        try:
            user = get_object(USER, user_id)
        except ObjectNotFoundError:
            return not_found(USER, user_id)

        try:
            user = load_request_into_object(USER)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username", str(user.uuid))

        return {'uuid': str(user.uuid), 'message': 'User {} updated'.format(user.username)}, 200

