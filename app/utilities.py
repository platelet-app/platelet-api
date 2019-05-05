from app import app, db, models
from app.views.functions.userfunctions import get_user_object, get_all_users
from app.views.functions.sessionfunctions import get_session_object, get_all_sessions
from app.views.functions.taskfunctions import get_task_object, get_all_tasks
from app.views.functions.vehiclefunctions import get_vehicle_object, get_all_vehicles
from app.views.functions.errors import already_flagged_for_deletion_error
from app.exceptions import ObjectNotFoundError


def add_item_to_delete_queue(item):
    if not item:
        return

    if item.flaggedForDeletion:
        return already_flagged_for_deletion_error("user", item.uuid)

    item.flaggedForDeletion = True

    delete = models.DeleteFlags(objectUUID=item.uuid, objectType=get_object_enum(item), timeToDelete=app.config['DEFAULT_DELETE_TIME'])

    db.session.add(item)
    db.session.add(delete)
    db.session.commit()

    return {'uuid': str(item.uuid), 'message': "{} queued for deletion".format(item)}, 202


def get_object_enum(item):
    if isinstance(item, models.User):
        return models.Objects.USER
    elif isinstance(item, models.Session):
        return models.Objects.SESSION
    elif isinstance(item, models.Task):
        return models.Objects.TASK
    elif isinstance(item, models.Vehicle):
        return models.Objects.VEHICLE
    else:
        raise ValueError("No corresponding enum to this object")

def object_type_to_string(type):

    switch = {
        models.Objects.SESSION: "session",
        models.Objects.USER: "user",
        models.Objects.TASK: "task",
        models.Objects.VEHICLE: "vehicle"
    }

    return switch.get(type, lambda: None)


def get_object(type, _id):

    try:
        if type == models.Objects.SESSION:
            return get_session_object(_id)
        elif type == models.Objects.USER:
            return get_user_object(_id)
        elif type == models.Objects.TASK:
            return get_task_object(_id)
        elif type == models.Objects.VEHICLE:
            return get_vehicle_object(_id)

    except ObjectNotFoundError:
        raise


def get_all_objects(type):

    switch = {
        models.Objects.SESSION: get_all_sessions(),
        models.Objects.USER: get_all_users(),
        models.Objects.TASK: get_all_tasks(),
        models.Objects.VEHICLE: get_all_vehicles()
    }

    obj = switch.get(type, lambda: None)

    if obj:
        return obj
    else:
        raise ObjectNotFoundError("There is no object of this type")
