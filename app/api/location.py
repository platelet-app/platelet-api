from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import location_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error
from app.utilities import get_object, add_item_to_delete_queue
from app.exceptions import ObjectNotFoundError

from app import db

LOCATION = models.Objects.LOCATION

locationSchema = schemas.LocationSchema()


@ns.route('/<location_id>', endpoint='location_detail')
class Location(Resource):
    @flask_praetorian.auth_required
    def get(self, location_id):
        if not location_id:
            return not_found("location", location_id)

        location = get_object(LOCATION, location_id)

        if (location):
            return jsonify(locationSchema.dump(location).data)
        else:
            return not_found(location_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, location_id):
        try:
            location = get_object(LOCATION, location_id)
        except ObjectNotFoundError:
            return not_found("location", location_id)

        return add_item_to_delete_queue(location)


@ns.route('s', endpoint='location_list')
class Locations(Resource):
    @flask_praetorian.roles_accepted('admin')
    def post(self):
        try:
            location = load_request_into_object(LOCATION)
        except Exception as e:
            return internal_error(e)

        db.session.add(location)
        db.session.commit()

        return {'uuid': str(location.uuid), 'message': 'Location {} created'.format(str(location.uuid))}, 201
