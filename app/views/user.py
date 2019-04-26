from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import schemas, db, models
from app import userApi as api
from flask_restful import Resource
import flask_praetorian
from app.views.functions.viewfunctions import user_id_match_or_admin, load_request_into_object
from app.views.functions.errors import not_found, schema_validation_error, not_unique_error
from app.exceptions import ObjectNotFoundError, SchemaValidationError
from app.utilities import add_item_to_delete_queue, get_object, get_all_objects

user_schema = schemas.UserSchema()
user_username_schema = schemas.UserUsernameSchema()
user_address_schema = schemas.UserAddressSchema()


class User(Resource):
    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def get(self, _id):
        try:
            user = get_object(models.Objects.USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        return jsonify(user_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def delete(self, _id):
        try:
            user = get_object(models.Objects.USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        return add_item_to_delete_queue(user)


api.add_resource(User,
                 '/<_id>')


class Users(Resource):

    @flask_praetorian.roles_accepted('admin')
    def get(self):
        users = get_all_objects(models.Objects.USER)

        user_id_username_list = []
        for i in users:
            user_id_username_list.append({"id": i.id, "username": i.username})

        return jsonify({'users': user_id_username_list})

    def post(self):
        user = models.User()
        try:
            load_request_into_object(user_schema, user)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username")

        return {'id': user.id, 'message': 'User {} created'.format(user.username)}, 201

api.add_resource(Users,
                 's')


class UserNameField(Resource):

    @flask_praetorian.auth_required
    def get(self, _id):
        try:
            user = get_object(models.Objects.USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        return jsonify(user_username_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, _id):
        try:
            user = get_object(models.Objects.USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        try:
            load_request_into_object(user_username_schema, user)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        try:
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username", user.id)

        return {'id': user.id, 'message': 'User {} updated'.format(user.username)}, 200

api.add_resource(UserNameField,
                 '/<_id>/username')


class UserAddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        try:
            user = get_object(models.Objects.USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        return jsonify(user_address_schema.dump(user).data)

    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def put(self, _id):
        try:
            user = get_object(models.Objects.USER, _id)
        except ObjectNotFoundError:
            return not_found("user", _id)

        try:
            load_request_into_object(user_address_schema, user)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        try:
            db.session.commit()
        except sqlexc.IntegrityError:
            return not_unique_error("username", user.id)

        return {'id': user.id, 'message': 'User {} updated'.format(user.username)}, 200

api.add_resource(UserAddressField,
                 '/<_id>/address')
