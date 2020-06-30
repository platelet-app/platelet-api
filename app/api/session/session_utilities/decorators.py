import functools
from flask_praetorian import utilities
from app.api.functions.errors import forbidden_error
from app import models


def session_id_match_or_admin(func):
    @functools.wraps(func)
    def wrapper(self, session_id):
        if 'admin' in utilities.current_rolenames():
            return func(self, session_id)
        if models.Session.query.filter_by(uuid=session_id).first().coordinator_uuid == utilities.current_user().uuid:
            return func(self, session_id)
        else:
            return forbidden_error("Object not owned by user: session id: {}".format(session_id))
    return wrapper


