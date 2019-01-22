from flask import jsonify
from app import schemas
from flask_restful import reqparse, Resource
import flask_praetorian
from app import vehicleApi as api
from app.views.functions.viewfunctions import *

from app import db

vehicleSchema = schemas.VehicleSchema()

class Vehicle(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return notFound()

        vehicle = getVehicleObject(_id)

        if (vehicle):
            return jsonify(vehicleSchema.dump(vehicle).data)
        else:
            return notFound(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        pass

class Vehicles(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):

        vehicle = models.Vehicle()
        error = loadRequestIntoObject(vehicleSchema, vehicle)

        if error:
            return error['errorMessage'], error['httpCode']

        if vehicle.dateOfManufacture > vehicle.dateOfRegistration:
            return forbiddenError("date of registration cannot be before date of manufacture")

        db.session.add(vehicle)
        db.session.commit()

        return {'id': vehicle.id, 'message': 'Vehicle {} created'.format(vehicle.id)}, 201

api.add_resource(Vehicle,
                 '/<_id>')
api.add_resource(Vehicles,
                 's')
def getVehicleObject(_id):
    return models.Vehicle.query.filter_by(id=_id).first()
