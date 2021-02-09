from flask import jsonify

from app import schemas, models
from flask_restx import Resource
import flask_praetorian
from app import location_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error, already_flagged_for_deletion_error
from app.api.functions.utilities import get_object, add_item_to_delete_queue, get_all_objects
from app.exceptions import ObjectNotFoundError, InvalidRangeError, AlreadyFlaggedForDeletionError

from app import db

LOCATION = models.Objects.LOCATION

location_schema = schemas.LocationSchema()
locations_schema = schemas.LocationSchema(many=True, only=("name", "uuid", "address"))


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

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    def patch(self, location_id):
        try:
            location = get_object(LOCATION, location_id)
            if location.deleted:
                return not_found(LOCATION, location_id)
        except ObjectNotFoundError:
            return not_found(LOCATION, location_id)

        load_request_into_object(LOCATION, instance=location)
        db.session.commit()
        return {'uuid': str(location.uuid), 'message': 'Location {} updated.'.format(location.uuid)}, 200


@ns.route('s', endpoint='location_list')
class Locations(Resource):
    def get(self):
        try:
            # TODO: decide if to paginate this or just return a basic list
            # parser = reqparse.RequestParser()
            # parser.add_argument("page", type=int, location="args")
            # parser.add_argument("order", type=str, location="args")
            # args = parser.parse_args()
            # page = args['page'] if args['page'] else 1
            # order = args['order'] if args['order'] else "newest"
            # items = get_page(get_query(LOCATION), page, order=order, model=models.Location)
            items = get_all_objects(LOCATION)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return jsonify(locations_schema.dump(items))

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    def post(self):
        try:
            location = load_request_into_object(LOCATION)
        except Exception as e:
            return internal_error(e)

        db.session.add(location)
        db.session.commit()

        return {'uuid': str(location.uuid), 'message': 'Location {} created'.format(str(location.uuid))}, 201
