from flask import Blueprint, request
from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import models
from app import ma
from app import schemas
from flask_restful import reqparse, abort, Api, Resource
from app import db
from app import api

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
sessionSchema = schemas.SessionSchema()

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
        for i in args:
            print(i)

        password = args['password']

        user = models.User(name=args['name'], username=args['username'], passwordHash=password, email=args['email'], dob=datetime.strptime(args['dob'], '%d/%m/%Y'), \
                           status=args['status'], assignedVehicle=int(args['vehicle']), \
                           patch=args['patch'], address1=args['address1'], address2=args['address2'], town=args['town'], county=args['county'], \
                           postcode=args['postcode'].upper(), country=args['country'])

        try:
            db.session.add(user)
            db.session.commit()
        except sqlexc.IntegrityError as e:
            return notUniqueError("username")

        return user.id, 201

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
                user.username = args['username']
                db.add(user)
                db.commit()
            except sqlexc.IntegrityError as e:
                return notUniqueError("username", user.id)
            finally:
                return {'id': user.id, 'message': "A database error has occurred"}


        else:
            return notFound(_id)

api.add_resource(User,
                 '/user/<_id>',
                 '/user/username/<_id>',
                 '/user/id/<_id>',
                 '/user')
api.add_resource(UserNameField,
                 '/user/username/<_id>',
                 '/user/username/username/<_id>')
api.add_resource(Users,
                 '/users')

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

    splitNum = len(api.prefix.split('/')) + 1
    
    if (request.path.split('/')[splitNum] == 'username'):
        return models.User.query.filter_by(username=_id).first()
    else:
        return models.User.query.filter_by(id=_id).first()


def getAllUsers():
    return models.User.query.all()


def notFound(id = "null"):
    return {'id': id, 'message': "The user was not found"}, 404


def databaseError(id = "null"):
    return {'id': id, 'message': "A database error has occurred"}, 500


def notUniqueError(field, id = "null"):
    return {'id': id, 'message': "{} not unique".format(field)}, 403
