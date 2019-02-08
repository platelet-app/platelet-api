from flask import jsonify
from app import schemas, models
from flask_restful import reqparse, Resource
import flask_praetorian
from app import taskApi as api
from app.views.functions.viewfunctions import load_request_into_object
from app.views.functions.errors import internal_error, not_found
from app.views.functions.taskfunctions import get_task_object

from app import db

taskSchema = schemas.TaskSchema()

class Task(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found()

        task = get_task_object(_id)

        if (task):
            return jsonify(taskSchema.dump(task).data)
        else:
            return not_found(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        pass

class Tasks(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):

        task = models.Task()
        try:
            load_request_into_object(taskSchema, task)
        except Exception as e:
            internal_error(e)

        db.session.add(task)
        db.session.commit()

        return {'id': task.id, 'message': 'Task {} created'.format(task.id)}, 201

api.add_resource(Task,
                 '/<_id>')
api.add_resource(Tasks,
                 's')

