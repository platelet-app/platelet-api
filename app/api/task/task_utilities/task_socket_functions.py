from flask import request
from flask_praetorian import utilities as prae_utils

from app.api.sockets import socketio
from app.api.task.task_utilities.task_socket_actions import ASSIGN_RIDER_TO_TASK, REMOVE_ASSIGNED_RIDER_FROM_TASK


def emit_socket_broadcast(data, type, uuid=None):
    try:
        tab_indentifier = request.headers['Tab-Identification']
    except KeyError:
        tab_indentifier = ""
    # TODO: when implementing organisations, maybe make a separate namespace for each one?
    socketio.socketIO.emit(
        'subscribed_response',
        {
            'object_uuid': str(uuid) if uuid else None,
            'type': type,
            'data': data,
            'tab_id': tab_indentifier,
            'calling_user_uuid': str(prae_utils.current_user().uuid),
            'calling_user_display_name': prae_utils.current_user().display_name
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

    room_identifier = "rider" if type == ASSIGN_RIDER_TO_TASK or type == REMOVE_ASSIGNED_RIDER_FROM_TASK else "coordinator"
    socketio.socketIO.emit(
        'subscribed_response',
        {
            'user_uuid': str(user_uuid),
            'type': type,
            'data': data,
            'tab_id': tab_indentifier,
            'calling_user_uuid': str(prae_utils.current_user().uuid),
            'calling_user_display_name': prae_utils.current_user().display_name
        },
        room="{}_{}".format(str(user_uuid), room_identifier),
        namespace="/api/v0.1/subscribe_assignments",
    )
