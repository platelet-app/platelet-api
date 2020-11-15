from flask import jsonify
from app import schemas, models
from flask_restx import Resource
import flask_praetorian
from app import root_ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error
from app.api.functions.utilities import get_object
from app.exceptions import ObjectNotFoundError

from app import db

SETTINGS = models.Objects.SETTINGS

server_settings_schema = schemas.ServerSettingsSchema()


@root_ns.route('/server_settings', endpoint='server_settings')
class ServerSettings(Resource):
    def get(self):
        try:
            settings = models.ServerSettings.query.filter_by(id=1).first()
            if not settings:
                return internal_error("There is no record in the database for server settings.")
            return jsonify(server_settings_schema.dump(settings))
        except Exception as e:
            return internal_error("An exception occurred while retrieving server settings: {}".format(e))

    @flask_praetorian.roles_required('admin')
    def put(self, vehicle_id):
        try:
            vehicle = get_object(SETTINGS, vehicle_id)
            if vehicle.deleted:
                return not_found(SETTINGS, vehicle_id)
        except ObjectNotFoundError:
            return not_found(SETTINGS, vehicle_id)

        load_request_into_object(SETTINGS, instance=vehicle)
        db.session.commit()
        return {'message': 'Server settings updated'}
