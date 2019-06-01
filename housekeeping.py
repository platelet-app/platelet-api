from app import models, app, db
from app.utilities import get_object
from datetime import datetime

flagged = models.DeleteFlags.query.filter_by(active=True).all()

current_time = datetime.utcnow()

items = [i for i in flagged if i.active and (current_time - i.timestamp).seconds > i.time_to_delete]

for i in items:
    i.active = False
    i.time_deleted = datetime.utcnow()
    db.session.delete(get_object(i.object_type, i.object_uuid))

db.session.commit()
