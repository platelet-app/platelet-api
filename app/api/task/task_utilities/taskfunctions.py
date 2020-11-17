from app import models, schemas, socketio
from flask import json, request
import hashlib

from app.exceptions import ObjectNotFoundError


def get_task_object(_id, with_deleted=False):
    if with_deleted:
        task = models.Task.query.with_deleted().filter_by(uuid=_id).first()
    else:
        task = models.Task.query.filter_by(uuid=_id).first()
    if not task:
        raise ObjectNotFoundError()
    return task


def set_previous_relay_uuids(task_parent):
    prev_task = None
    for i in sorted(task_parent.relays_with_deleted, key=lambda t: t.order_in_relay):
        if i.deleted:
            i.relay_previous_uuid = None
            continue
        if prev_task:
            i.relay_previous_uuid = prev_task.uuid
        else:
            i.relay_previous_uuid = None

        prev_task = i

    return task_parent


def get_task_parent_object(_id, with_deleted):
    if with_deleted:
        task_parent = models.TasksParent.query.with_deleted().filter_by(id=_id).first()
    else:
        task_parent = models.TasksParent.query.filter_by(id=_id).first()
    if not task_parent:
        raise ObjectNotFoundError()
    return task_parent


def get_all_tasks(filter_deleted=False):
    if filter_deleted:
        return models.Task.query.all()
    else:
        return models.Task.query.with_deleted().all()


def calculate_tasks_etag(data):
    tasks_schema = schemas.TaskSchema(many=True)
    json_data = json.dumps(tasks_schema.dump(data))
    return hashlib.sha1(bytes(json_data, 'utf-8')).hexdigest()


def emit_socket_broadcast(data, type, uuid=None):
    try:
        tab_indentifier = request.headers['Tab-Identification']
    except KeyError:
        tab_indentifier = ""
    # TODO: when implementing organisations, maybe make a separate namespace for each one?
    socketio.emit(
        'subscribed_response',
        {
            'object_uuid': str(uuid) if uuid else None,
            'type': type,
            'data': data,
            'tab_id': tab_indentifier
        },
        room=str(uuid) if uuid else "root",
        namespace="/api/v0.1/subscribe",
    )


def emit_socket_assignment_broadcast(data, type, user_uuid):
    # TODO: when implementing organisations, maybe make a separate namespace for each one?
    try:
        tab_indentifier = request.headers['Tab-Identification']
    except KeyError:
        tab_indentifier = ""
    socketio.emit(
        'subscribed_response',
        {
            'user_uuid': str(user_uuid),
            'type': type,
            'data': data,
            'tab_id': tab_indentifier
        },
        room=str(user_uuid),
        namespace="/api/v0.1/subscribe_assignments",
    )
