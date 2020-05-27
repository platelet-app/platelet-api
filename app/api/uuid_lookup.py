from flask import jsonify
import flask_praetorian
from app import schemas, any_object_ns as ns, models
from flask_restx import Resource
from app.exceptions import ObjectNotFoundError
from app.utilities import get_object
from app.api.functions.errors import not_found

user_dump_schema = schemas.UserSchema(exclude=("password",))
vehicle_schema = schemas.VehicleSchema()
session_schema = schemas.SessionSchema()
task_schema = schemas.TaskSchema()
comment_schema = schemas.CommentSchema()
deliverable_schema = schemas.DeliverableSchema()
location_schema = schemas.LocationSchema()

@ns.route('/<object_id>',
          endpoint='any_object_detail')
class AnyObject(Resource):
    @flask_praetorian.auth_required
    def get(self, object_id):
        obj = None
        for i in models.Objects:
            try:
                obj = get_object(i, object_id)
                if obj:
                    break
            except ObjectNotFoundError:
                continue

        if not obj:
            return not_found(None, object_id)
        else:
            if obj.object_type == models.Objects.USER:
                return jsonify(user_dump_schema.dump(obj).data)
            if obj.object_type == models.Objects.SESSION:
                return jsonify(session_schema.dump(obj).data)
            if obj.object_type == models.Objects.VEHICLE:
                return jsonify(vehicle_schema.dump(obj).data)
            if obj.object_type == models.Objects.TASK:
                return jsonify(task_schema.dump(obj).data)
            if obj.object_type == models.Objects.NOTE:
                return jsonify(note_schema.dump(obj).data)
            if obj.object_type == models.Objects.LOCATION:
                return jsonify(location_schema.dump(obj).data)
            if obj.object_type == models.Objects.DELIVERABLE:
                return jsonify(deliverable_schema.dump(obj).data)
