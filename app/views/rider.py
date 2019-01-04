from flask import Blueprint, request
from flask import jsonify
from app import models
from flask_restful import reqparse, abort, Api, Resource
from app import db
from app import api

from datetime import datetime

parser = reqparse.RequestParser()
#parser.add_argument('name', 'username', 'email', 'dob', 'status', 'assignedVehicle', 'patch')
parser.add_argument('name')
parser.add_argument('username')
parser.add_argument('email')
parser.add_argument('dob')
parser.add_argument('status')
parser.add_argument('vehicle')
parser.add_argument('patch')

mod = Blueprint('rider', __name__, url_prefix='/api/v1/rider/')

class Rider(Resource):


    def get(self, id):
        rider = getRiderObject(id)


        if (rider):
            return { 'id': rider.id, 'name': rider.name, 'patch': rider.patch,
                           'dob': datetime.strftime(rider.dob, '%d/%m/%Y'), 'vehicle': rider.assignedVehicle, 'status': rider.status,
                           'address1': rider.address1, 'address2': rider.address2,
                           'town': rider.town, 'county': rider.county,
                           'postcode': rider.postcode, 'country': rider.country }
        else:
            return notFound()

class RiderCreator(Resource):

    def post(self):

        args = parser.parse_args()
        for i in args:
            print(i)
            
        rider = models.Rider(name=args['name'], email=args['email'], dob=datetime.strptime(args['dob'], '%d/%m/%Y'),\
                             status=args['status'], assignedVehicle=int(args['vehicle']),\
                             patch=args['patch'])
        db.session.add(rider)
        db.session.commit()

        return rider.id, 201
    

api.add_resource(Rider, '/rider/<id>')
api.add_resource(RiderCreator, '/rider/')

@mod.route('<int:id>/name', methods=['GET'])
def getRiderName(id):
    rider = getRiderObject(id)

    if (rider):
        return jsonify(id=rider.id, name=rider.name)
    else:
        return notFound()


@mod.route('<int:id>/address', methods=['GET'])
def getRiderAddress(id):
    rider = getRiderObject(id)

    if (rider):
        return jsonify(id=rider.id, address1=rider.address1, address2=rider.address2,
        town=rider.town, county=rider.county,
        postcode=rider.postcode, country=rider.country)
    else:
        return notFound()


@mod.route('<int:id>/status', methods=['GET'])
def getRiderStatus(id):
    rider = getRiderObject(id)

    if (rider):
        return jsonify(id=rider.id, status=rider.status)
    else:
        return notFound()


@mod.route('<int:id>/vehicle', methods=['GET'])
def getRiderVehicle(id):
    rider = getRiderObject(id)

    if (rider):
        return jsonify(id=rider.id, status=rider.assignedVehicle)
    else:
        return notFound()


@mod.route('<int:id>/availability', methods=['GET'])
def getRiderAvailability(id):
    return "WHAT IS THIS I DUNNO LOL {}".format(id)


@mod.route('<int:id>/patch', methods=['GET'])
def getRiderPatch(id):
    rider = getRiderObject(id)

    if (rider):
        return jsonify(id=rider.id, status=rider.patch)
    else:
        return notFound()


@mod.route('submit', methods=['POST'])
def saveRider():

    for i in request.form:
        print(i)

    return "saved... lol not really"


@mod.route('edit', methods=['POST'])
def editRider():
    return "edited... lol not realllly"

def getRiderObject(id):
    return models.Rider.query.filter_by(id=id).first()

def notFound():
    return jsonify(id=0)
