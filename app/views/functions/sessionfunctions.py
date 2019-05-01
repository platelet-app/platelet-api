import functools
from flask_praetorian import utilities
from app import models
from app.exceptions import ObjectNotFoundError
from app.views.functions.errors import forbidden_error


def session_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        if models.Session.query.filter_by(uuid=_id).first().user_id == utilities.current_user_id():
            return func(self, _id)
        else:
            return forbidden_error("Object not owned by user: session id:".format(_id))
    return wrapper


def get_session_object(_id):
    session = models.Session.query.filter_by(uuid=_id).first()
    if not session:
        raise ObjectNotFoundError("session id:{} not found".format(_id))
    return session

def get_all_sessions():
    sessions = models.Session.query.all()
    if not sessions:
        return {}
    return sessions
