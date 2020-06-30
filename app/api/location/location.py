from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import location_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error, already_flagged_for_deletion_error
from app.utilities import get_object, add_item_to_delete_queue, get_all_objects, get_range
from app.exceptions import ObjectNotFoundError, InvalidRangeError, AlreadyFlaggedForDeletionError

from app import db

LOCATION = models.Objects.LOCATION

location_schema = schemas.LocationSchema()
locations_schema = schemas.LocationSchema(many=True)


@ns.route('/<location_id>', endpoint='location_detail')
class Location(Resource):
    @flask_praetorian.auth_required
    def get(self, location_id):
        try:
            return jsonify(location_schema.dump(get_object(LOCATION, location_id)))
        except ObjectNotFoundError:
            return not_found(LOCATION, location_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, location_id):
        try:
            location = get_object(LOCATION, location_id)
        except ObjectNotFoundError:
            return not_found("location", location_id)
        try:
            add_item_to_delete_queue(location)
        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(LOCATION, str(location.uuid))

        return add_item_to_delete_queue(location)

    @flask_praetorian.roles_required('admin', 'coordinator')
    def put(self, location_id):
        try:
            location = get_object(LOCATION, location_id)
            if location.flagged_for_deletion:
                return not_found(LOCATION, location_id)
        except ObjectNotFoundError:
            return not_found(LOCATION, location_id)

        load_request_into_object(LOCATION, instance=location)
        db.session.commit()
        return {'uuid': str(location.uuid), 'message': 'Location {} updated.'.format(location.uuid)}, 200


@ns.route('s', endpoint='location_list')
class Locations(Resource):
    def get(self, _range=None, order="ascending"):
        try:
            items = get_range(get_all_objects(LOCATION), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return jsonify(locations_schema.dump(items))
    @flask_praetorian.roles_accepted('admin')
    def post(self):
        try:
            location = load_request_into_object(LOCATION)
        except Exception as e:
            return internal_error(e)

        db.session.add(location)
        db.session.commit()

        return {'uuid': str(location.uuid), 'message': 'Location {} created'.format(str(location.uuid))}, 201
