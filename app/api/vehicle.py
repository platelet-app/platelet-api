from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import vehicle_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error
from app.utilities import get_object, add_item_to_delete_queue
from app.exceptions import ObjectNotFoundError

from app import db

VEHICLE = models.Objects.VEHICLE

vehicleSchema = schemas.VehicleSchema()


@ns.route('/<uuid>', endpoint='vehicle_detail')
class Vehicle(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found()

        vehicle = get_object(VEHICLE, _id)

        if (vehicle):
            return jsonify(vehicleSchema.dump(vehicle).data)
        else:
            return not_found(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        try:
            vehicle = get_object(VEHICLE, _id)
        except ObjectNotFoundError:
            return not_found("vehicle", _id)

        return add_item_to_delete_queue(vehicle)


@ns.route('s', endpoint='vehicle_list')
class Vehicles(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):

        try:
            vehicle = load_request_into_object(VEHICLE)
        except Exception as e:
            return internal_error(e)

        if vehicle.dateOfManufacture > vehicle.dateOfRegistration:
            return forbidden_error("date of registration cannot be before date of manufacture")

        db.session.add(vehicle)
        db.session.commit()

        return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} created'.format(str(vehicle.uuid))}, 201

