from flask import Blueprint, render_template

from app import db

mod = Blueprint('rider', __name__, url_prefix='/api/v1/rider')

@mod.route('<int:id>', methods=['GET'])
def getRider(id):
    return "The rider for ID {}".format(id)


@mod.route('<int:id>/name', methods=['GET'])
def getRiderName(id):
    return "The name of the rider for ID {}".format(id)


@mod.route('<int:id>/address', methods=['GET'])
def getRiderAddress(id):
    return "The address of the rider for ID {}".format(id)


@mod.route('<int:id>/status', methods=['GET'])
def getRiderStatus(id):
    return "The status of the rider for ID {}".format(id)


@mod.route('<int:id>/vehicle', methods=['GET'])
def getRiderVehicle(id):
    return "The vehicle of the rider for ID {}".format(id)


@mod.route('<int:id>/availability', methods=['GET'])
def getRiderAvailability(id):
    return "The availability of the rider for ID {}".format(id)


@mod.route('<int:id>/patch', methods=['GET'])
def getRiderPatch(id):
    return "The patch of the rider for ID {}".format(id)


@mod.route('submit', methods=['PUT'])
def saveRider():
    return "saved... lol not really"


@mod.route('edit', methods=['POST'])
def editRider():
    return "edited... lol not realllly"

