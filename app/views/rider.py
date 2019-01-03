from flask import Blueprint, render_template
from flask import jsonify
from app import models
from flask_restful import reqparse, abort, Api, Resource
from app import db
from app import api

parser = reqparse.RequestParser()
parser.add_argument('rider')

mod = Blueprint('rider', __name__, url_prefix='/api/v1/rider/')

class Rider(Resource):


    def get(self, id):
        rider = getRiderObject(id)


        if (rider):
            return { 'id': rider.id, 'name': rider.name, 'patch': rider.patch,
                           'dob': rider.dob, 'vehicle': rider.assignedVehicle, 'status': rider.status,
                           'address1': rider.address1, 'address2': rider.address2,
                           'town': rider.town, 'county': rider.county,
                           'postcode': rider.postcode, 'country': rider.country }
        else:
            return notFound()


    def put(self, id):
        args = parser.parse_args()


api.add_resource(Rider, '/rider/<id>')

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


@mod.route('submit', methods=['PUT'])
def saveRider():
    return "saved... lol not really"


@mod.route('edit', methods=['POST'])
def editRider():
    return "edited... lol not realllly"

def getRiderObject(id):
    return models.Rider.query.filter_by(id=id).first()

def notFound():
    return jsonify(id=0)
