from app import models
from app.exceptions import ObjectNotFoundError

def get_note_object(_id):
    result = models.Note.query.filter_by(uuid=_id).first()
    if not result:
        raise ObjectNotFoundError("note id: {} not found".format(_id))
    return result
