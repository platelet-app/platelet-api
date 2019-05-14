from app import models

def get_note_object(_id):
    return models.Deliverable.query.filter_by(uuid=_id).first()
