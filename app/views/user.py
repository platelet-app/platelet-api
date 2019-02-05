from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import schemas
from flask_restful import Resource
import flask_praetorian
from app.views.functions.userfunctions import *
from app.views.functions.viewfunctions import *
from app.views.functions.errors import *

userSchema = schemas.UserSchema()
userAddressSchema = schemas.UserAddressSchema()

deleteTime = 60 * 60 # TODO

class User(Resource):
    @flask_praetorian.auth_required
    @userIdMatchOrAdmin
    def get(self, _id):
        if not _id:
            return notFound("user")

        user = getUserObject(_id)
        if not user:
            return notFound("user", _id)

        return userSchema.dumps(user)


    @flask_praetorian.auth_required
    @userIdMatchOrAdmin
    def delete(self, _id):
        if not _id:
            return notFound("user")

        user = getUserObject(_id)
        if not user:
            return notFound("user", _id)

        if user.flaggedForDeletion:
            return forbiddenError("this user is already flagged for deletion")

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
        users = getAllUsers()
        if not users:
            return notFound("user")

        usersList = {}
        for i in users:
            usersList.update({i.id: i.username})

        return jsonify({'users': usersList})

    def post(self):
        user = models.User()
        try:
            loadRequestIntoObject(userSchema, user)
        except Exception as e:
            return internalError(e)

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return notUniqueError("username")

        return {'id': user.id, 'message': 'User {} created'.format(user.username)}, 201

api.add_resource(Users,
                 's')


class UserNameField(Resource):

    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return notFound("user")

        user = getUserObject(_id)
        if not user:
            return notFound("user", _id)

        return {'id': user.id, 'name': user.name}

    @flask_praetorian.auth_required
    def put(self, _id):
        user = getUserObject(_id)
        if not user:
            return notFound("user", _id)

        try:
            loadRequestIntoObject(userSchema, user)
        except Exception as e:
            return internalError(e)

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return notUniqueError("username", user.id)
        except Exception as e:
            return databaseError(_id)

        return {'id': user.id, 'message': 'User {} updated'.format(user.username)}, 200

api.add_resource(UserNameField,
                 '/username/<_id>',
                 '/username/username/<_id>',
                 '/id/username/<_id>')


class AddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        user = getUserObject(_id)
        if not user:
            return notFound("user", _id)
        return userAddressSchema.dumps(user)

    @flask_praetorian.auth_required
    def put(self, _id):
        user = getUserObject(_id)
        if not user:
            return notFound("user", _id)

        try:
            loadRequestIntoObject(userAddressSchema, user)
        except Exception as e:
            return internalError(e)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            return databaseError(_id)

        return userAddressSchema.dumps(user)

api.add_resource(AddressField,
                 '<_id>/address',
                 '/username/<_id>/address',
                 '/id/<_id>/address')

