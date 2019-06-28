from flask import jsonify
from app import schemas, models
from flask_restplus import reqparse, Resource
import flask_praetorian
from app import task_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import internal_error, not_found
from app.utilities import add_item_to_delete_queue, get_object
from app.exceptions import ObjectNotFoundError

from app import db

taskSchema = schemas.TaskSchema()

TASK = models.Objects.TASK


@ns.route('/<task_id>', endpoint="task_detail")
class Task(Resource):
    @flask_praetorian.auth_required
    def get(self, task_id):
        if not task_id:
            return not_found(TASK)

        task = get_object(TASK, task_id)

        if (task):
            return jsonify(taskSchema.dump(task).data)
        else:
            return not_found(TASK, task_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK)
        return add_item_to_delete_queue(task)

    @flask_praetorian.roles_required('admin', 'coordinator')
    def put(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        new_data = load_request_into_object(TASK)
        models.Session.query.filter_by(uuid=task_id).update(new_data)
        db.session.commit()
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200


@ns.route('s', endpoint="tasks_list")
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


