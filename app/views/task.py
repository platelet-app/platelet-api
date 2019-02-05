from flask import jsonify
from app import schemas
from flask_restful import reqparse, Resource
import flask_praetorian
from app import taskApi as api
from app.views.functions.viewfunctions import *
from app.views.functions.errors import *

from app import db

taskSchema = schemas.TaskSchema()

class Task(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return notFound()

        task = getTaskObject(_id)

        if (task):
            return jsonify(taskSchema.dump(task).data)
        else:
            return notFound(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        pass

class Tasks(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):

        task = models.Task()
        try:
            loadRequestIntoObject(taskSchema, task)
        except Exception as e:
            internalError(e)

        db.session.add(task)
        db.session.commit()

        return {'id': task.id, 'message': 'Task {} created'.format(task.id)}, 201

api.add_resource(Task,
                 '/<_id>')
api.add_resource(Tasks,
                 's')
def getTaskObject(_id):
    return models.Task.query.filter_by(id=_id).first()

