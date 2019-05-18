from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import schemas, db, models
from app import userApi as api
from flask_restful import Resource, reqparse
import flask_praetorian
from app.api.functions.viewfunctions import user_id_match_or_admin, load_request_into_object
from app.api.functions.errors import not_found, schema_validation_error, not_unique_error
from app.exceptions import ObjectNotFoundError, SchemaValidationError
from app.utilities import add_item_to_delete_queue, get_object, get_all_objects
from app import guard

USER = models.Objects.USER

user_dump_schema = schemas.UserSchema(exclude=("password",))
user_schema = schemas.UserSchema()
users_schema = schemas.UserSchema(many=True, exclude=('address', 'dob', 'email', 'notes', 'password', 'name', 'roles', 'patch'))
address_schema = schemas.AddressSchema()
user_username_schema = schemas.UserUsernameSchema()
user_address_schema = schemas.UserAddressSchema()


class User(Resource):
    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def get(self, uuid):
        try:
            user = get_object(USER, uuid)
        except ObjectNotFoundError:
            return not_found("user", uuid)
        except:
            raise

        return jsonify(user_dump_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def delete(self, uuid):
        print("ASDFJKL;ASDFJKL;")
        try:
            print("ASDFJKL;ASDFJKL;")
            user = get_object(USER, uuid)
            print("ASDFJKL;ASDFJKL;")
        except ObjectNotFoundError:
            return not_found("user", uuid)

        print("ASDFJKL;ASDFJKL;")
        return add_item_to_delete_queue(user)


api.add_resource(User,
                 '/<uuid>',
                 endpoint='user')


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

api.add_resource(Users,
                 '',
                 's',
                 endpoint='users')


class UserNameField(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        try:
            user = get_object(USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        return jsonify(user_username_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, _id):

        parser = reqparse.RequestParser()
        parser.add_argument('username')
        args = parser.parse_args()
        try:
            user = get_object(USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        if args['username']:
            user.username = args['username']

        else:
            return schema_validation_error("No data")

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username", user.id)

        return {'uuid': str(user.uuid), 'message': 'User {} updated'.format(user.username)}, 200

api.add_resource(UserNameField,
                 '/<_id>/username')


class UserAddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        try:
            user = get_object(USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        return jsonify(user_address_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, _id):
        try:
            user = get_object(USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        try:
            #user.address = load_request_into_object(USER).address
            user = load_request_into_object(USER)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username", user.id)

        return {'uuid': str(user.uuid), 'message': 'User {} updated'.format(user.username)}, 200

api.add_resource(UserAddressField,
                 '/<_id>/address')
