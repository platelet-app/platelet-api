import flask_praetorian
from flask import jsonify
from app.api.functions.errors import internal_error
from app.api.functions.utilities import get_all_objects
from flask_restx import Resource
from app import root_ns
from app import models
from app import schemas

priorities_schema = schemas.PrioritySchema(many=True)

PRIORITY = models.Objects.PRIORITY


@root_ns.route('/priorities', endpoint='priorities_list')
class Priorities(Resource):
    @flask_praetorian.auth_required
    def get(self):
        try:
            items = get_all_objects(PRIORITY)
        except Exception as e:
            return internal_error(e)

        return jsonify(priorities_schema.dump(items))

