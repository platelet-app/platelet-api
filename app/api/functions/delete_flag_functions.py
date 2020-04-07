from app import models

def get_delete_flag_object(_id):
    return models.DeleteFlags.query.filter_by(uuid=_id).first()
