from app import models, schemas, socketio
from flask import json, request
import hashlib
from app.exceptions import ObjectNotFoundError


def get_task_object(_id):
    task = models.Task.query.filter_by(uuid=_id).first()
    if not task:
        raise ObjectNotFoundError()
    return task


def get_task_parent_object(_id):
    task_parent = models.TasksParent.query.filter_by(id=_id).first()
    if not task_parent:
        raise ObjectNotFoundError()
    return task_parent


def get_all_tasks(filter_deleted=False):
    if filter_deleted:
        return models.Task.query.filter_by(flagged_for_deletion=False)
    else:
        return models.Task.query.all()


def calculate_tasks_etag(data):
    tasks_schema = schemas.TaskSchema(many=True)
    json_data = json.dumps(tasks_schema.dump(data))
    return hashlib.sha1(bytes(json_data, 'utf-8')).hexdigest()


def emit_socket_broadcast(data, type, uuid=None):
    # TODO: when implementing organisations, maybe make a separate namespace for each one?
    socketio.emit(
        'subscribed_response',
        {
            'object_uuid': str(uuid) if uuid else None,
            'type': type,
            'data': data,
            'tab_id': request.headers['Tab-Identification']
        },
        room=str(uuid) if uuid else "root",
        namespace="/api/v0.1/subscribe",
    )


def emit_socket_assignment_broadcast(data, type, user_uuid):
    # TODO: when implementing organisations, maybe make a separate namespace for each one?
    socketio.emit(
        'subscribed_response',
        {
            'user_uuid': str(user_uuid),
            'type': type,
            'data': data,
            'tab_id': request.headers['Tab-Identification']
        },
        room=str(user_uuid),
        namespace="/api/v0.1/subscribe_assignments",
    )
