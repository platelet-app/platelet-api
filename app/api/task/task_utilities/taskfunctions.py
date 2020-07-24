from app import models, schemas, socketio
from flask import json, request
import hashlib
from app.exceptions import ObjectNotFoundError


def get_task_object(_id):
    task = models.Task.query.filter_by(uuid=_id).first()
    if not task:
        raise ObjectNotFoundError()
    return task


def get_all_tasks():
    tasks = models.Task.query.all()
    if not tasks:
        return {}
    return tasks


def calculate_tasks_etag(data):
    tasks_schema = schemas.TaskSchema(many=True)
    json_data = json.dumps(tasks_schema.dump(data))
    return hashlib.sha1(bytes(json_data, 'utf-8')).hexdigest()


def emit_socket_broadcast(data, uuid, type):
    socketio.emit('subscribed_response',
                  {
                      'object_uuid': str(uuid),
                      'type': type,
                      'data': data,
                      'tab_id': request.headers['Tab-Identification']
                  },
                  room=str(uuid),
                  namespace="/api/v0.1/subscribe")
