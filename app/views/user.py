from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import schemas, db, models
from app import userApi as api
from flask_restful import Resource
import flask_praetorian
from app.views.functions.userfunctions import get_user_object, get_all_users
from app.views.functions.viewfunctions import user_id_match_or_admin, load_request_into_object
from app.views.functions.errors import not_found, forbidden_error, internal_error, not_unique_error, database_error
from app.exceptions import ObjectNotFoundError

from app.utilities import get_object

userSchema = schemas.UserSchema()
userAddressSchema = schemas.UserAddressSchema()


class User(Resource):
    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def get(self, _id):
        if not _id:
            return not_found("user")

        try:
            user = get_user_object(_id)
        except ObjectNotFoundError as e:
            return not_found("user", _id)
        except Exception as e:
            # this should probably be logged instead of returned
            return internal_error(e)

        return userSchema.dumps(user)


    @flask_praetorian.auth_required
    @user_id_match_or_admin
    def delete(self, _id):
        if not _id:
            return not_found("user")

        user = get_user_object(_id)
        if not user:
            return not_found("user", _id)

        if user.flaggedForDeletion:
            return forbidden_error("this user is already flagged for deletion")

        user.flaggedForDeletion = True

        delete = models.DeleteFlags(objectId=_id, objectType=models.Objects.USER, timeToDelete=10)

        db.session.add(user)
        db.session.add(delete)

        db.session.commit()

        return {'id': _id, 'message': "User {} queued for deletion".format(user.username)}, 202

api.add_resource(User,
                 '',
                 '/<_id>',
                 '/username/<_id>',
                 '/id/<_id>')


class Users(Resource):

    @flask_praetorian.auth_required
    def get(self):
        users = get_all_users()
        if not users:
            return not_found("user")

        usersList = []
        for i in users:
            usersList.append({"id": i.id, "username": i.username})

        return jsonify({'users': usersList})

    def post(self):
        user = models.User()
        try:
            load_request_into_object(userSchema, user)
        except Exception as e:
            return internal_error(e)

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return not_unique_error("username")

        return {'id': user.id, 'message': 'User {} created'.format(user.username)}, 201

api.add_resource(Users,
                 's')


class UserNameField(Resource):

    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found("user")

        user = get_user_object(_id)
        if not user:
            return not_found("user", _id)

        return {'id': user.id, 'name': user.name}

    @flask_praetorian.auth_required
    def put(self, _id):
        user = get_user_object(_id)
        if not user:
            return not_found("user", _id)

        try:
            load_request_into_object(userSchema, user)
        except Exception as e:
            return internal_error(e)

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return not_unique_error("username", user.id)
        except Exception as e:
            return database_error(_id)

        return {'id': user.id, 'message': 'User {} updated'.format(user.username)}, 200

api.add_resource(UserNameField,
                 '/username/<_id>',
                 '/username/username/<_id>',
                 '/id/username/<_id>')


class AddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        user = get_user_object(_id)
        if not user:
            return not_found("user", _id)
        return userAddressSchema.dumps(user)

    @flask_praetorian.auth_required
    def put(self, _id):
        user = get_user_object(_id)
        if not user:
            return not_found("user", _id)

        try:
            load_request_into_object(userAddressSchema, user)
        except Exception as e:
            return internal_error(e)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            return database_error(_id)

        return userAddressSchema.dumps(user)

api.add_resource(AddressField,
                 '<_id>/address',
                 '/username/<_id>/address',
                 '/id/<_id>/address')

