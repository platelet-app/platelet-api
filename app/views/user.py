from flask import request
import json
from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import models
from app import schemas
from flask_restful import reqparse, abort, Api, Resource
import flask_praetorian
from app import db
from app import userApi as api
from app import guard
from .viewfunctions import *

userSchema = schemas.UserSchema()
userAddressSchema = schemas.UserAddressSchema()

deleteTime = 60 * 60 # TODO

class User(Resource):
    @flask_praetorian.auth_required
    @userIdMatchOrAdmin
    def get(self, _id):
        if not _id:
            return notFound()

        user = getUserObject(_id)
        if not user:
            return notFound(_id)

        return userSchema.dumps(user)


    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        if not _id:
            return notFound()

        user = getUserObject(_id)
        if not user:
            return notFound(_id)

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
            return notFound()

        usersList = {}
        for i in users:
            usersList.update({i.id: i.username})

        return jsonify({'users': usersList})

    @flask_praetorian.roles_required('admin')
    def post(self):
        user = models.User()
        error = loadRequestIntoObject(userSchema, user)

        if error:
            return error['errorMessage'], error['httpCode']

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
            return notFound()

        user = getUserObject(_id)
        if not user:
            return notFound(_id)

        return {'id': user.id, 'name': user.name}

    @flask_praetorian.auth_required
    def put(self, _id):
        user = getUserObject(_id)
        if not user:
            return notFound(_id)

        error = loadRequestIntoObject(userSchema, user)
        if error:
            return error['errorMessage'], error['httpCode']

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
            return notFound(_id)
        return userAddressSchema.dumps(user)

    @flask_praetorian.auth_required
    def put(self, _id):
        user = getUserObject(_id)
        if not user:
            return notFound(_id)

        error = loadRequestIntoObject(userAddressSchema, user)
        if error:
            return error['errorMessage'], error['httpCode']

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


def loadRequestIntoObject(schema, objectToLoadInto):
    requestJson = request.get_json()
    if not requestJson:
        return {'errorMessage' : {'message': "No json input data provided"}, 'httpCode': 400}

    parsedSchema = schema.load(requestJson)
    if parsedSchema.errors:
        return {'errorMessage' : json.dumps(parsedSchema.errors), 'httpCode': 400}  # TODO better error formatting

    objectToLoadInto.updateFromDict(**parsedSchema.data)

    return None


def getUserObject(_id):

    splitNum = len(api.prefix.split('/'))
    
    if (request.path.split('/')[splitNum] == 'username'):
        return models.User.query.filter_by(username=_id).first()
    else:
        return models.User.query.filter_by(id=_id).first()


def getAllUsers():
    return models.User.query.all()

def notFound(id = "null"):
    return {'id': id, 'message': "The user was not found"}, 404


def databaseError(id = "null"):
    traceback.print_exception(*sys.exc_info())
    return {'id': id, 'message': "A database error has occurred"}, 500


def notUniqueError(field, id = "null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403
