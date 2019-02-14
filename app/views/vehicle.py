from flask import jsonify
from app import schemas, models
from flask_restful import reqparse, Resource
import flask_praetorian
from app import vehicleApi as api
from app.views.functions.vehiclefunctions import get_vehicle_object
from app.views.functions.viewfunctions import load_request_into_object
from app.views.functions.errors import not_found, internal_error, forbidden_error

from app import db

vehicleSchema = schemas.VehicleSchema()

class Vehicle(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found()

        vehicle = get_vehicle_object(_id)

        if (vehicle):
            return jsonify(vehicleSchema.dump(vehicle).data)
        else:
            return not_found(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        pass

class Vehicles(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):

        vehicle = models.Vehicle()
        try:
            load_request_into_object(vehicleSchema, vehicle)
        except Exception as e:
            return internal_error(e)

        if vehicle.dateOfManufacture > vehicle.dateOfRegistration:
            return forbidden_error("date of registration cannot be before date of manufacture")

        db.session.add(vehicle)
        db.session.commit()

        return {'id': vehicle.id, 'message': 'Vehicle {} created'.format(vehicle.id)}, 201

api.add_resource(Vehicle,
                 '/<_id>')
api.add_resource(Vehicles,
                 's')
