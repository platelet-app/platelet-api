from flask import request

from app.api.comment.comment_utilities.comment_socket_actions import ADD_COMMENT
from app.api.sockets import socketio


def emit_socket_comment_broadcast(data, type, parent_uuid, uuid=None):
    try:
        tab_indentifier = request.headers['Tab-Identification']
    except KeyError:
        return
    # try:
    #     if not data['publicly_visible']:
    #         print(data['author_uuid'], socketio.user_uuid)
    #         if not str(socketio.user_uuid) == data['author_uuid']:
    #             return
    # except KeyError:
    #     return
    if type == ADD_COMMENT:
        socketio.socketIO.emit(
            'subscribed_response',
            {
                'parent_uuid': str(parent_uuid),
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
            room=str(parent_uuid),
            namespace="/api/v0.1/subscribe_comments"
        )
