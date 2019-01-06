from flask import Blueprint, request
from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import models
from app import ma
from app import schemas
from flask_restful import reqparse, abort, Api, Resource
from app import db
from app import userApi as api
import sys
import traceback

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

userSchema = schemas.UserSchema()
userAddressSchema = schemas.UserAddressSchema()
sessionSchema = schemas.SessionSchema()

deleteTime = 60 * 60

mod = Blueprint('user', __name__, url_prefix='/api/v1/user/')

class User(Resource):


    def get(self, _id):
        user = getUserObject(_id)

        if (user):
            return jsonify(userSchema.dump(user).data)
        else:
            return notFound(_id)

    def post(self):

        args = parser.parse_args()

        password = args['password']

        user = models.User()

        try:
            db.session.add(saveValues(user, args))
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return notUniqueError("username")

        return user.id, 201

    def delete(self, _id):

        user = getUserObject(_id)
        user.flaggedForDeletion = True

        delete = models.deleteFlags(objectId=10, objectType=10, timeToDelete=10)

        db.session.add(user)
        db.session.add(delete)

        db.session.commit()

        return {'id': _id}, 204

class Users(Resource):


    def get(self):
        users = getAllUsers()

        usersList = {}

        for i in users:
            usersList.update({i.id: i.username})

        if (users):
            return jsonify({'users': usersList})
        else:
            return notFound()

class UserNameField(Resource):
    
    def get(self, _id):
        user = getUserObject(_id)
        
        if (user):
            return {'id': user.id, 'name': user.name}
        else:
            return notFound(_id)

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
    def get(self, _id):
        user = getUserObject(_id)

        if (user):
            return jsonify(userAddressSchema.dump(user).data)
        else:
            return notFound(_id)

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
                 's' )
api.add_resource(UserNameField,
                 '/username/<_id>',
                 '/username/username/<_id>',
                 '/id/username/<_id>')
api.add_resource(AddressField,
                 '/address/<_id>',
                 '/username/address/<_id>',
                 '/id/address/<_id>')


@mod.route('<int:id>/name', methods=['GET'])
def getUserName(id):
    user = getUserObject(id)

    if (user):
        return jsonify(id=user.id, name=user.name)
    else:
        return notFound()


@mod.route('<int:id>/address', methods=['GET'])
def getUserAddress(id):
    user = getUserObject(id)

    if (user):
        return jsonify(id=user.id, address1=user.address1, address2=user.address2,
        town=user.town, county=user.county,
        postcode=user.postcode, country=user.country)
    else:
        return notFound()


@mod.route('<int:id>/status', methods=['GET'])
def getUserStatus(id):
    user = getUserObject(id)

    if (user):
        return jsonify(id=user.id, status=user.status)
    else:
        return notFound(id)


@mod.route('<int:id>/vehicle', methods=['GET'])
def getUserVehicle(id):
    user = getUserObject(id)

    if (user):
        return jsonify(id=user.id, status=user.assignedVehicle)
    else:
        return notFound()


@mod.route('<int:id>/availability', methods=['GET'])
def getUserAvailability(id):
    return "WHAT IS THIS I DUNNO LOL {}".format(id)


@mod.route('<int:id>/patch', methods=['GET'])
def getUserPatch(id):
    user = getUserObject(id)

    if (user):
        return jsonify(id=user.id, status=user.patch)
    else:
        return notFound()


@mod.route('submit', methods=['POST'])
def saveUser():

    for i in request.form:
        print(i)

    return "saved... lol not really"


@mod.route('edit', methods=['POST'])
def editUser():
    return "edited... lol not realllly"

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

def saveValues(user, args):

    if args['name']: user.name = args['name']
    if args['username']: user.username = args['username']
    if args['email']: user.email = args['email']
    if args['patch']: user.email = args['email']
    if args['dob']: user.dob = datetime.strptime(args['dob'], '%d/%m/%Y')
    if args['status']: user.status = args['status']
    if args['address1']: user.address1 = args['address1']
    if args['address2']: user.address2 = args['address2']
    if args['town']: user.town = args['town']
    if args['county']: user.county = args['county']
    if args['country']: user.country = args['country']
    if args['postcode']: user.postcode = args['postcode'].upper()

    return user
