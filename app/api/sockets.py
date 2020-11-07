from flask_socketio import emit, join_room, leave_room
from app import socketio
from app import api_version
from threading import Lock

thread = None
thread_lock = Lock()

namespace = "/api/{}/subscribe".format(api_version)
namespace_comments = "/api/{}/subscribe_comments".format(api_version)
namespace_assignments = "/api/{}/subscribe_assignments".format(api_version)

UPDATE_TASK = "UPDATE_TASK"
ASSIGN_RIDER_TO_TASK = "ASSIGN_RIDER_TO_TASK"
REMOVE_ASSIGNED_RIDER_FROM_TASK = "REMOVE_ASSIGNED_RIDER_FROM_TASK"
ASSIGN_COORDINATOR_TO_TASK = "ASSIGN_COORDINATOR_TO_TASK"
REMOVE_ASSIGNED_COORDINATOR_FROM_TASK = "REMOVE_ASSIGNED_COORDINATOR_FROM_TASK"
ADD_NEW_TASK = "ADD_NEW_TASK"
DELETE_TASK = "DELETE_TASK"
RESTORE_TASK = "RESTORE_TASK"


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
