from flask import request

from app.api.comment.comment_utilities.comment_socket_actions import ADD_COMMENT
from app.api.sockets import socketio


def emit_socket_comment_broadcast(data, type, parent_uuid, uuid=None):
    try:
        tab_indentifier = request.headers['Tab-Identification']
    except KeyError:
        tab_indentifier = ""
    if type == ADD_COMMENT:
        socketio.socketIO.emit(
            'subscribed_response',
            {
                'parent_uuid': str(uuid),
                'type': type,
                'data': data,
                'tab_id': tab_indentifier
            },
            room=str(parent_uuid),
            namespace="/api/v0.1/subscribe_comments"
        )
    else:
        socketio.socketIO.emit(
            'subscribed_response',
            {
                'uuid': str(uuid),
                'type': type,
                'data': data,
                'tab_id': tab_indentifier
            },
            room=str(parent_uuid) ,
            namespace="/api/v0.1/subscribe_comments"
        )
