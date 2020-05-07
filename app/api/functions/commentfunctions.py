import functools
from flask_praetorian import utilities
from app import models
from app.api.functions.errors import forbidden_error
from app.exceptions import ObjectNotFoundError


def comment_author_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        comment_author = models.Comment.query.filter_by(uuid=_id).first().author_uuid
        if utilities.current_user().uuid == comment_author:
            return func(self, _id)
        else:
            return forbidden_error("Comment not owned by user: user id: {}".format(comment_author))
    return wrapper


def get_comment_object(_id):
    result = models.Comment.query.filter_by(uuid=_id).first()
    if not result:
        raise ObjectNotFoundError("comment id: {} not found".format(_id))
    return result
