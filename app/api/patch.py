import flask_praetorian
from flask import jsonify, request
from app.api.functions.errors import internal_error
from app.utilities import get_range, get_all_objects
from flask_restx import Resource
from app import root_ns
from app import models
from app import schemas

patches_schema = schemas.PatchSchema(many=True)

PATCH = models.Objects.PATCH


@root_ns.route('/patches', endpoint='patches_list')
class Patches(Resource):
    @flask_praetorian.auth_required
    def get(self):
        try:
            items = get_all_objects(PATCH)
        except Exception as e:
            return internal_error(e)

        return jsonify(patches_schema.dump(items))

