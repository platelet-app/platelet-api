import json

from flask import jsonify
from flask_socketio import emit, join_room, leave_room
from app import socketio, models, schemas
from app import api_version
from threading import Lock

from app.api.functions.utilities import get_object
from app.api.task.task_utilities.task_socket_actions import TASKS_REFRESH

thread = None
thread_lock = Lock()

namespace = "/api/{}/subscribe".format(api_version)
namespace_comments = "/api/{}/subscribe_comments".format(api_version)
namespace_assignments = "/api/{}/subscribe_assignments".format(api_version)

TASK = models.Objects.TASK
tasks_schema = schemas.TaskSchema(exclude=("assigned_coordinators", "comments"))


@socketio.on('refresh_data', namespace=namespace)
def check_etags(uuid_etag_dict):
    result = []
    for entry, etag in uuid_etag_dict.items():
        task = get_object(TASK, entry)
        dump = tasks_schema.dump(task)
        if dump['etag'] != etag:
            result.append(dump)
    emit('request_response', {
        'data': json.dumps({"tasks": result}),
        'type': TASKS_REFRESH
    })


@socketio.on('subscribe', namespace=namespace)
def subscribe_to_object(obj_uuid):
    join_room(obj_uuid)
    emit('response', {'data': "Subscribed to object with uuid {}.".format(obj_uuid)})


@socketio.on('subscribe_many', namespace=namespace)
def subscribe_to_objects(uuids_list):
    for i in uuids_list:
        join_room(i)
    emit('response', {'data': "Subscribed to {} objects".format(len(uuids_list))})


@socketio.on('unsubscribe_many', namespace=namespace)
def unsubscribe_from_objects(uuids_list):
    for i in uuids_list:
        leave_room(i)
    emit('response', {'data': "Unsubscribed from {} objects".format(len(uuids_list))})


@socketio.on('unsubscribe', namespace=namespace)
def unsubscribe_from_object(obj_uuid):
    leave_room(obj_uuid)
    emit('response', {'data': "Unsubscribed from object with uuid {}.".format(obj_uuid)})


@socketio.on('subscribe', namespace=namespace_comments)
def subscribe_to_comments(obj_uuid):
    join_room(obj_uuid)
    emit('response', {'data': "Subscribed to comments for object with uuid {}.".format(obj_uuid)})


@socketio.on('unsubscribe', namespace=namespace_comments)
def unsubscribe_from_comments(obj_uuid):
    leave_room(obj_uuid)
    emit('response', {'data': "Unsubscribed from comments for object with uuid {}.".format(obj_uuid)})


@socketio.on('subscribe', namespace=namespace_assignments)
def subscribe_to_comments(user_uuid):
    join_room(user_uuid)
    emit('response', {'data': "Subscribed to assignments for user with uuid {}.".format(user_uuid)})


@socketio.on('unsubscribe', namespace=namespace_assignments)
def unsubscribe_from_comments(user_uuid):
    leave_room(user_uuid)
    emit('response', {'data': "Unsubscribed from assignments for user with uuid {}.".format(user_uuid)})


@socketio.on('connect', namespace=namespace)
def test_connect():
    print("client connected")
    emit('my response', {'data': 'Connected'})


@socketio.on('disconnect', namespace=namespace)
def test_disconnect():
    print('Client disconnected')


@socketio.on('authenticated', namespace=namespace)
def test_authenticated():
    print('Authed')
