from flask import request
from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import models
from app import ma
from app import schemas
from flask_restful import reqparse, abort, Api, Resource
import flask_praetorian
from flask_praetorian import utilities
from app import db
from app import userApi as api
from app import guard
from .viewfunctions import *
import functools
import inspect

from datetime import datetime

parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('username')
parser.add_argument('password')
parser.add_argument('email')
parser.add_argument('dob')
parser.add_argument('status')
parser.add_argument('vehicle')
parser.add_argument('patch')
parser.add_argument('address1')
parser.add_argument('address2')
parser.add_argument('town')
parser.add_argument('county')
parser.add_argument('postcode')
parser.add_argument('country')
parser.add_argument('roles')
parser.add_argument('active')

userSchema = schemas.UserSchema()
userAddressSchema = schemas.UserAddressSchema()
sessionSchema = schemas.SessionSchema()

deleteTime = 60 * 60




class User(Resource):
    @flask_praetorian.auth_required
    @userIdMatch
    def get(self, _id):


        if not _id:
            return notFound()

        user = getUserObject(_id)

        if (user):
            return jsonify(userSchema.dump(user).data)
        else:
            return notFound(_id)


    @flask_praetorian.roles_required('admin')
    def delete(self, _id):

        user = getUserObject(_id)

        user.flaggedForDeletion = True

        delete = models.DeleteFlags(objectId=_id, objectType=models.Objects.USER, timeToDelete=10)

        db.session.add(user)
        db.session.add(delete)

        db.session.commit()

        return {'id': _id, 'message': "User {} queued for deletion".format(user.username)}, 202


class Users(Resource):

    @flask_praetorian.auth_required
    def get(self):
        users = getAllUsers()

        usersList = {}

        for i in users:
            usersList.update({i.id: i.username})

        if (users):
            return jsonify({'users': usersList})
        else:
            return notFound()

    @flask_praetorian.roles_required('admin')
    def post(self):

        args = parser.parse_args()
        user = models.User()

        try:
            db.session.add(saveValues(user, args))
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return notUniqueError("username")

        return {'id': user.id, 'message': 'User {} created'.format(user.username)}, 201

class UserNameField(Resource):

    @flask_praetorian.auth_required
    def get(self, _id):
        user = getUserObject(_id)
        
        if (user):
            return {'id': user.id, 'name': user.name}
        else:
            return notFound(_id)

    @flask_praetorian.auth_required
    def put(self, _id):
        user = getUserObject(_id)

        if (user):
            args = parser.parse_args()
            try:
                db.session.add(saveValues(user, args))
                db.session.commit()
            except sqlexc.IntegrityError as e:
                return notUniqueError("username", user.id)
            except Exception as e:
                return databaseError(_id)


        else:
            return notFound(_id)


class AddressField(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        user = getUserObject(_id)

        if (user):
            return jsonify(userAddressSchema.dump(user).data)
        else:
            return notFound(_id)

    @flask_praetorian.auth_required
    def put(self, _id):

        user = getUserObject(_id)

        if user:
            args = parser.parse_args()
            try:
                db.session.add(saveValues(user, args))
                db.session.commit()

                return jsonify(userAddressSchema.dump(user).data)

            except Exception as e:
                print(e)
                return databaseError(_id)


        else:
            return notFound(_id)

api.add_resource(User,
                 '',
                 '/<_id>',
                 '/username/<_id>',
                 '/id/<_id>')
api.add_resource(Users,
                 's')
api.add_resource(UserNameField,
                 '/username/<_id>',
                 '/username/username/<_id>',
                 '/id/username/<_id>')
api.add_resource(AddressField,
                 '<_id>/address',
                 '/username/<_id>/address',
                 '/id/<_id>/address')


def getUserObject(_id):

    splitNum = len(api.prefix.split('/'))
    
    if (request.path.split('/')[splitNum] == 'username'):
        return models.User.query.filter_by(username=_id).first()
    else:
        return models.User.query.filter_by(id=_id).first()


def getAllUsers():
    return models.User.query.all()



def saveValues(user, args):

    if args['name']: user.name = args['name']
    if args['username']: user.username = args['username']
    if args['email']: user.email = args['email']
    if args['patch']: user.patch = args['patch']
    if args['dob']: user.dob = datetime.strptime(args['dob'], '%d/%m/%Y')
    if args['status']: user.status = args['status']
    if args['address1']: user.address1 = args['address1']
    if args['address2']: user.address2 = args['address2']
    if args['town']: user.town = args['town']
    if args['county']: user.county = args['county']
    if args['country']: user.country = args['country']
    if args['postcode']: user.postcode = args['postcode'].upper()
    if args['password']: user.password = guard.encrypt_password(args['password'])
    if args['roles']: user.roles = args['roles'].lower()
    if args['active']: user.is_active = True if args['roles'].lower() == 'yes' else False

    return user
