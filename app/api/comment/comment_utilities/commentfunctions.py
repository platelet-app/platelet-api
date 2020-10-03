import functools
from flask_praetorian import utilities
from app import models, schemas, socketio
from app.api.functions.errors import forbidden_error
from app.exceptions import ObjectNotFoundError
from flask import json, request
import hashlib

def comment_author_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        comment_author = models.Comment.query.filter_by(uuid=_id).first().author_uuid
        if utilities.current_user().uuid == comment_author:
            return func(self, _id)
        else:
            return forbidden_error("Comment {} not owned by user: {}".format(_id, comment_author))
    return wrapper


def get_comment_object(_id):
    result = models.Comment.query.filter_by(uuid=_id).first()
    if not result:
        raise ObjectNotFoundError("comment id: {} not found".format(_id))
    return result


def calculate_comments_etag(data):
    comments_schema = schemas.CommentSchema(many=True)
    json_data = json.dumps(comments_schema.dump(data))
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
                  namespace="/api/v0.1/subscribe_comments",
                  )
