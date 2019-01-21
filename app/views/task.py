from flask import Blueprint
from flask import jsonify
from app import schemas
from flask_restful import reqparse, Resource
import flask_praetorian
from app import taskApi as api
from app.views.functions.viewfunctions import *

from app import db

parser = reqparse.RequestParser()
parser.add_argument('pickupAddressOne')
parser.add_argument('pickupAddressTwo')
parser.add_argument('pickupAddressTown')
parser.add_argument('pickupTown')
parser.add_argument('pickupPostcode')
parser.add_argument('destinationAddressOne')
parser.add_argument('destinationAddressTwo')
parser.add_argument('destinationTown')
parser.add_argument('destinationPostcode')
parser.add_argument('patch')
parser.add_argument('contactName')
parser.add_argument('contactNumber')
parser.add_argument('priority')
parser.add_argument('session')

taskSchema = schemas.TaskSchema()

mod = Blueprint('task', __name__, url_prefix='/api/v1/task')

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
        error = loadRequestIntoObject(taskSchema, task)

        if error:
            return error['errorMessage'], error['httpCode']

        db.session.add(task)
        db.session.commit()

        return {'id': task.id, 'message': 'Task {} created'.format(task.id)}, 201

api.add_resource(Task,
                 '/<_id>')
api.add_resource(Tasks,
                 's')
def getTaskObject(_id):
    return models.Task.query.filter_by(id=_id).first()

