from app import models
from app.exceptions import ObjectNotFoundError


def get_session_object(_id):
    session = models.Session.query.filter_by(uuid=_id).first()
    if not session:
        raise ObjectNotFoundError("session id: {} not found".format(_id))
    return session


def get_all_sessions():
    sessions = models.Session.query.all()
    if not sessions:
        return {}
    return sessions
