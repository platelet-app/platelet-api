from app import models

def get_deliverable_object(_id):
    return models.Deliverable.query.filter_by(uuid=_id).first()
