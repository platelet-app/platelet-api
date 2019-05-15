from flask import jsonify
from app import schemas, models
from flask_restful import reqparse, Resource
import flask_praetorian
from app import taskApi as api
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import internal_error, not_found
from app.utilities import add_item_to_delete_queue, get_object
from app.exceptions import ObjectNotFoundError

from app import db

taskSchema = schemas.TaskSchema()

TASK = models.Objects.TASK

class Task(Resource):
    @flask_praetorian.auth_required
    def get(self, uuid):
        if not uuid:
            return not_found(TASK)

        task = get_object(TASK, uuid)

        if (task):
            return jsonify(taskSchema.dump(task).data)
        else:
            return not_found(TASK, uuid)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        try:
            task = get_object(TASK, _id)
        except ObjectNotFoundError:
            return not_found(TASK)
        return add_item_to_delete_queue(task)

class Tasks(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        task = None
        try:
            task = load_request_into_object(TASK)
        except Exception as e:
            internal_error(e)

        db.session.add(task)
        db.session.commit()

        return {'uuid': str(task.uuid), 'message': 'Task {} created'.format(task.uuid)}, 201

api.add_resource(Task,
                 '/<uuid>', endpoint="task_detail")
api.add_resource(Tasks,
                 's', endpoint="tasks_list")

