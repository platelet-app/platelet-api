import functools
from flask_praetorian import utilities
from app import models
from app.exceptions import ObjectNotFoundError
from app.views.functions.errors import unauthorised_error


def session_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        if models.Session.query.filter_by(id=_id).first().user_id == utilities.current_user_id():
            return func(self, _id)
        else:
            return unauthorised_error("Object not owned by user: session id:".format(_id))
    return wrapper


def get_session_object(_id):
    user = models.Session.query.filter_by(id=_id).first()
    if not user:
        raise ObjectNotFoundError("session id:{} not found".format(_id))
    return user
