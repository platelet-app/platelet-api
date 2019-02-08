from app import app, db, models
from app.views.functions.userfunctions import get_user_object
from app.views.functions.sessionfunctions import get_session_object

def getObject(type, _id):
    switch = {
        models.Objects.SESSION: get_session_object(_id),
        models.Objects.USER: get_user_object(_id)
    }

    obj = switch.get(type, lambda: None)

    if obj:
        return obj
    else:
        raise Exception("There is no object of this type")