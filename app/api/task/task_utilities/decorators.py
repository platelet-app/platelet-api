import functools
from flask_praetorian import utilities
from app.api.functions.errors import forbidden_error, internal_error
from app import models


def check_rider_match(func):
    @functools.wraps(func)
    def wrapper(self, task_id):
        if "coordinator" in utilities.current_rolenames() or "admin" in utilities.current_rolenames():
            return func(self, task_id)
        assigned_riders = models.Task.query.filter_by(uuid=task_id).first().assigned_users
        if utilities.current_user().uuid in [rider.uuid for rider in assigned_riders]:
            return func(self, task_id)
        else:
            return forbidden_error("Calling user is not a coordinator or assigned user.")
    return wrapper


def check_parent_or_collaborator_or_admin_match(func):
    @functools.wraps(func)
    def wrapper(self, task_id, **kwargs):
        try:
            if kwargs["skip_collab_check"]:
                return func(self, task_id)
        except KeyError:
            pass
        if "admin" in utilities.current_rolenames():
            return func(self, task_id)
        calling_user_uuid = utilities.current_user().uuid
        task = models.Task.query.filter_by(uuid=task_id).first()
        if task.parent_session:
            if calling_user_uuid == task.parent_session.coordinator_uuid:
                return func(self, task_id)
            elif calling_user_uuid in [user.uuid for user in task.parent_session.collaborators]:
                return func(self, task_id)
            else:
                return forbidden_error(
                    "Parent session is not owned by calling user or collaborator: session id: {}".format(
                        task.parent_session.uuid)
                )
        else:
            return internal_error("There is no parent session for this task.")

    return wrapper


def check_parent_or_admin_match(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if "admin" in utilities.current_rolenames():
            return func(self, *args)
        calling_user_uuid = utilities.current_user().uuid
        task = models.Task.query.filter_by(uuid=args[0]).first()
        if task.parent_session:
            if calling_user_uuid == task.parent_session.coordinator_uuid:
                return func(self, *args, **kwargs)
            else:
                return forbidden_error(
                    "Parent session is not owned by calling user or collaborator: session id: {}".format(
                        task.parent_session.uuid)
                )
        else:
            return internal_error("There is no parent session for this task.")

    return wrapper
