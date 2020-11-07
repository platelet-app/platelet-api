from app import db, models
from app.api.functions.utilities import get_object
import datetime

delete_time = 60 * 60 # TODO

def monitor_deletions():

        queue = models.DeleteFlags.query.all()

        for i in queue:
            if i.timestamp < datetime.datetime.now() - datetime.timedelta(seconds=60):
                object = get_object(i.objectType, i.objectId)
                #db.session.delete(i)

        db.session.commit()

