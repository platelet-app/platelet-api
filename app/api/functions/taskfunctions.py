from app import models
from app.exceptions import ObjectNotFoundError

def get_task_object(_id):
    task = models.Task.query.filter_by(uuid=_id).first()
    if not task:
        raise ObjectNotFoundError()
    return task

def get_all_tasks():
    tasks = models.Task.query.all()
    if not tasks:
        return {}
    return tasks
