from app import app, db, models
from app.views.functions.userfunctions import getUserObject
from app.views.functions.sessionfunctions import getSessionObject

def getObject(type, _id):
    switch = {
        models.Objects.SESSION: getSessionObject(_id),
        models.Objects.USER: getUserObject(_id)
    }

    obj = switch.get(type, lambda: None)

    if obj:
        return obj
    else:
        raise Exception("There is no object of this type")