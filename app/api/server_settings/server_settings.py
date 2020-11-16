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
    def patch(self, settings_id):
        try:
            settings = get_object(SETTINGS, settings_id)
        except ObjectNotFoundError:
            return not_found(SETTINGS, settings_id)

        load_request_into_object(SETTINGS, instance=settings)
        db.session.commit()
        return {'message': 'Server settings updated'}
