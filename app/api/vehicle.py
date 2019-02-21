from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import vehicle_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error, schema_validation_error
from app.utilities import get_object, add_item_to_delete_queue
from app.exceptions import ObjectNotFoundError, SchemaValidationError

from app import db

VEHICLE = models.Objects.VEHICLE

vehicle_schema = schemas.VehicleSchema()


@ns.route('/<vehicle_id>', endpoint='vehicle_detail')
class Vehicle(Resource):
    @flask_praetorian.auth_required
    def get(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)

        return jsonify(vehicle_schema.dump(vehicle).data)

    @flask_praetorian.roles_required('admin')
    def delete(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)

        return add_item_to_delete_queue(vehicle)

    @flask_praetorian.roles_required('admin')
    def put(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)

        new_data = load_request_into_object(VEHICLE)
        models.Session.query.filter_by(uuid=vehicle_id).update(new_data)
        db.session.commit()
        return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} updated.'.format(vehicle.uuid)}, 200


@ns.route('s', endpoint='vehicle_list')
class Vehicles(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        try:
            vehicle = load_request_into_object(VEHICLE)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        db.session.add(vehicle)
        db.session.commit()

        return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} created'.format(str(vehicle.uuid))}, 201

