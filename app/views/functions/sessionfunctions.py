import functools
from flask_praetorian import utilities
from app import models

def sessionIdMatchOrAdmin(func):
    @functools.wraps(func)
    def wrapper(self, _id):
        if 'admin' in utilities.current_rolenames():
            return func(self, _id)
        if models.Session.query.filter_by(id=_id).first().user_id == utilities.current_user_id():
            return func(self, _id)
        else:
            return {"id": _id, "message": "Object not owned by user"}, 401
    return wrapper

def getSessionObject(_id):
    return models.User.query.filter_by(id=_id).first()


