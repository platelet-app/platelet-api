from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import task_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import internal_error, not_found, forbidden_error, schema_validation_error
from app.utilities import add_item_to_delete_queue, get_object, get_range
from app.exceptions import ObjectNotFoundError, InvalidRangeError, SchemaValidationError

from app import db

task_schema = schemas.TaskSchema()
tasks_schema = schemas.TaskSchema(many=True, exclude=('contact_name', 'contact_number', 'deliverables', 'dropoff_address', 'notes', 'pickup_address'))

TASK = models.Objects.TASK
SESSION = models.Objects.SESSION


@ns.route('/<task_id>', endpoint="task_detail")
class Task(Resource):
    @flask_praetorian.auth_required
    def get(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        return jsonify(task_schema.dump(task).data)

    @flask_praetorian.roles_required('admin')
    def delete(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

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


@ns.route('s',
          's/<session_id>',
          endpoint="tasks_list")
class Tasks(Resource):
    @flask_praetorian.auth_required
    def get(self, session_id, _range=None, order="ascending"):
        try:
            session = get_object(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        try:
            items = get_range(session.tasks.all(), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return tasks_schema.jsonify(items)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        try:
            task = load_request_into_object(TASK)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))

        db.session.add(task)
        db.session.commit()

        return {'uuid': str(task.uuid), 'message': 'Task {} created'.format(task.uuid)}, 201
