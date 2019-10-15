from app import models
from app.exceptions import ObjectNotFoundError
import functools
from flask_praetorian import utilities
from app.api.functions.errors import forbidden_error
from app.api.functions.userfunctions import get_user_object_by_int_id

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

def check_rider_match(func):
    @functools.wraps(func)
    def wrapper(self, task_id):
        if "coordinator" in utilities.current_rolenames() or "admin" in utilities.current_rolenames():
            return func(self, task_id)
        if models.Task.query.filter_by(uuid=task_id).first().assigned_rider == get_user_object_by_int_id(utilities.current_user_id()).uuid:
            return func(self, task_id)
        else:
            return forbidden_error("Task not owned by user: session id: {}".format(task_id))
    return wrapper
