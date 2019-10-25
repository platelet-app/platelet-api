from app import app, db, models
from app.api.functions.userfunctions import get_user_object, get_all_users
from app.api.functions.sessionfunctions import get_session_object, get_all_sessions
from app.api.functions.taskfunctions import get_task_object, get_all_tasks
from app.api.functions.vehiclefunctions import get_vehicle_object, get_all_vehicles
from app.api.functions.locationfunctions import get_location_object, get_all_locations
from app.api.functions.priorityfunctions import get_all_priorities
from app.api.functions.notefunctions import get_note_object
from app.api.functions.deliverablefunctions import get_deliverable_object, get_all_deliverable_types
from app.api.functions.errors import already_flagged_for_deletion_error
from app.exceptions import ObjectNotFoundError, InvalidRangeError


def add_item_to_delete_queue(item):
    if not item:
        return

    if item.flagged_for_deletion:
        return already_flagged_for_deletion_error(item.object_type, str(item.uuid))

    item.flagged_for_deletion = True

    delete = models.DeleteFlags(object_uuid=item.uuid, object_type=item.object_type, time_to_delete=app.config['DEFAULT_DELETE_TIME'])

    db.session.add(item)
    db.session.commit()
    db.session.add(delete)
    db.session.commit()

    return {'uuid': str(item.uuid), 'message': "{} queued for deletion".format(item)}, 202  # TODO does item need to be converted to string?


def object_type_to_string(type):
    switch = {
        models.Objects.SESSION: "session",
        models.Objects.USER: "user",
        models.Objects.TASK: "task",
        models.Objects.VEHICLE: "vehicle",
        models.Objects.NOTE: "note",
        models.Objects.DELIVERABLE: "deliverable",
        models.Objects.LOCATION: "location"
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
        elif type == models.Objects.NOTE:
            return get_note_object(_id)
        elif type == models.Objects.DELIVERABLE:
            return get_deliverable_object(_id)
        elif type == models.Objects.LOCATION:
            return get_location_object(_id)

    except ObjectNotFoundError:
        raise


def get_all_objects(type):

    switch = {
        models.Objects.SESSION: get_all_sessions(),
        models.Objects.USER: get_all_users(),
        models.Objects.TASK: get_all_tasks(),
        models.Objects.VEHICLE: get_all_vehicles(),
        models.Objects.LOCATION: get_all_locations(),
        models.Objects.PRIORITY: get_all_priorities(),
        models.Objects.DELIVERABLE_TYPE: get_all_deliverable_types()
    }

    obj = switch.get(type, lambda: None)

    if obj is not None:
        return obj
    else:
        raise ObjectNotFoundError("There is no object of this type")


def get_range(items, _range="0-100", order="descending"):

    start = 0
    end = 100

    if _range:
        between = _range.split('-')

        if between[0].isdigit() and between[1].isdigit():
            start = int(between[0])
            end = int(between[1])
        else:
            raise InvalidRangeError("invalid range")

    if start > end:
        raise InvalidRangeError("invalid range")

    if end - start > 1000:
        raise InvalidRangeError("range too large")

    if order == "descending":
        items.reverse()

    result = [i for i in items if not i.flagged_for_deletion]


    return result[start:end]
