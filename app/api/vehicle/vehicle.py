from flask import jsonify
from app import schemas, models
from flask_restx import Resource, reqparse
import flask_praetorian
from app import vehicle_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error, schema_validation_error, \
    already_flagged_for_deletion_error
from app.utilities import get_object, add_item_to_delete_queue, get_range, get_all_objects, remove_item_from_delete_queue, \
    get_page, get_query
from app.exceptions import ObjectNotFoundError, SchemaValidationError, InvalidRangeError, AlreadyFlaggedForDeletionError

from app import db

VEHICLE = models.Objects.VEHICLE

vehicle_schema = schemas.VehicleSchema()
vehicles_schema = schemas.VehicleSchema(many=True)


@ns.route('/<vehicle_id>/restore', endpoint="vehicle_undelete")
class VehicleRestore(Resource):
    @flask_praetorian.roles_accepted("admin")
    def put(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)

        if vehicle.flagged_for_deletion:
            remove_item_from_delete_queue(vehicle)
        else:
            return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} not flagged for deletion.'.format(vehicle.uuid)}, 200
        return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} deletion flag removed.'.format(vehicle.uuid)}, 200


@ns.route('/<vehicle_id>', endpoint='vehicle_detail')
class Vehicle(Resource):
    @flask_praetorian.auth_required
    def get(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
            return vehicle_schema.dump(vehicle)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)
        try:
            add_item_to_delete_queue(vehicle)
        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(VEHICLE, str(vehicle.uuid))

        return {'uuid': str(vehicle.uuid), 'message': "Vehicle queued for deletion"}, 202

    @flask_praetorian.roles_required('admin')
    def put(self, vehicle_id):
        try:
            vehicle = get_object(VEHICLE, vehicle_id)
            if vehicle.flagged_for_deletion:
                return not_found(VEHICLE, vehicle_id)
        except ObjectNotFoundError:
            return not_found(VEHICLE, vehicle_id)

        load_request_into_object(VEHICLE, instance=vehicle)
        db.session.commit()
        return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} updated.'.format(vehicle.uuid)}, 200


@ns.route('s', endpoint='vehicle_list')
class Vehicles(Resource):
    @flask_praetorian.auth_required
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("page", type=int, location="args")
            parser.add_argument("order", type=str, location="args")
            args = parser.parse_args()
            page = args['page'] if args['page'] else 1
            order = args['order'] if args['order'] else "newest"
            items = get_page(get_query(VEHICLE), page, order=order, model=models.Vehicle)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return vehicles_schema.dump(items)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        try:
            vehicle = load_request_into_object(VEHICLE)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        db.session.add(vehicle)
        db.session.commit()

        return {'uuid': str(vehicle.uuid), 'message': 'Vehicle {} created'.format(str(vehicle.uuid))}, 201

