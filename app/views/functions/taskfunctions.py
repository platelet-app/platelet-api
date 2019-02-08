from app import models

def get_task_object(_id):
    return models.Task.query.filter_by(id=_id).first()
