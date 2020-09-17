import logging

from sqlalchemy import desc, asc

from app import app, db, models
from app.api.user.user_utilities.userfunctions import get_user_object, get_all_users
from app.api.task.task_utilities.taskfunctions import get_task_object, get_all_tasks
from app.api.vehicle.vehicle_utilities.vehiclefunctions import get_vehicle_object, get_all_vehicles
from app.api.location.location_utilities.locationfunctions import get_location_object, get_all_locations
from app.api.priority.priority_utilities.priorityfunctions import get_all_priorities
from app.api.patch.patch_utilities.patchfunctions import get_all_patches
from app.api.comment.comment_utilities.commentfunctions import get_comment_object
from app.api.functions.delete_flag_functions import get_delete_flag_object
from app.api.deliverable.deliverable_utilities.deliverablefunctions import get_deliverable_object, get_all_deliverable_types
from app.exceptions import ObjectNotFoundError, InvalidRangeError, AlreadyFlaggedForDeletionError


def remove_item_from_delete_queue(item):
    if not item:
        return
    flag = get_object(models.Objects.DELETE_FLAG, item.uuid)
    if flag:
        db.session.delete(flag)
        item.flagged_for_deletion = False
        db.session.commit()


def add_item_to_delete_queue(item):
    if not item:
        return

    if item.flagged_for_deletion:
        raise AlreadyFlaggedForDeletionError("This item is already flagged for deletion")

    item.flagged_for_deletion = True

    delete = models.DeleteFlags(uuid=item.uuid, object_type=item.object_type, time_to_delete=app.config['DEFAULT_DELETE_TIME'])

    db.session.add(delete)
    db.session.commit()


def object_type_to_string(type):
    switch = {
        models.Objects.SESSION: "session",
        models.Objects.USER: "user",
        models.Objects.TASK: "task",
        models.Objects.VEHICLE: "vehicle",
        models.Objects.COMMENT: "comment",
        models.Objects.DELIVERABLE: "deliverable",
        models.Objects.LOCATION: "location"
    }

    return switch.get(type, lambda: None)


def get_unspecified_object(_id):
    if not _id:
        raise ObjectNotFoundError

    for i in models.Objects:
        try:
            return get_object(i, _id)
        except ObjectNotFoundError:
            continue

    raise ObjectNotFoundError


def get_object(type, _id):
    if not _id:
        raise ObjectNotFoundError

    try:
        if type == models.Objects.USER:
            return get_user_object(_id)
        elif type == models.Objects.TASK:
            return get_task_object(_id)
        elif type == models.Objects.VEHICLE:
            return get_vehicle_object(_id)
        elif type == models.Objects.COMMENT:
            return get_comment_object(_id)
        elif type == models.Objects.DELIVERABLE:
            return get_deliverable_object(_id)
        elif type == models.Objects.LOCATION:
            return get_location_object(_id)
        elif type == models.Objects.DELETE_FLAG:
            return get_delete_flag_object(_id)

    except ObjectNotFoundError:
        raise


def get_query(model_type, filter_deleted=True):
    switch = {
        models.Objects.USER: models.User.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.User.query,
        models.Objects.TASK: models.Task.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.Task.query,
        models.Objects.VEHICLE: models.Vehicle.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.Vehicle.query,
        models.Objects.LOCATION: models.Location.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.Location.query,
        models.Objects.PRIORITY: models.Priority.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.Priority.query,
        models.Objects.PATCH: models.Patch.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.Patch.query,
        models.Objects.DELIVERABLE_TYPE: models.Deliverable.query.filter_by(flagged_for_deletion=False) if filter_deleted else models.Deliverable.query,
    }

    items = switch.get(model_type, lambda: None)

    if items is None:
        raise ObjectNotFoundError("There is no object of this type")
    else:
        return items


def get_all_objects(model_type, filter_deleted=False):

    switch = {
        models.Objects.USER: get_all_users(filter_deleted=filter_deleted),
        models.Objects.TASK: get_all_tasks(filter_deleted=filter_deleted),
        models.Objects.VEHICLE: get_all_vehicles(filter_deleted=filter_deleted),
        models.Objects.LOCATION: get_all_locations(filter_deleted=filter_deleted),
        models.Objects.PRIORITY: get_all_priorities(filter_deleted=filter_deleted),
        models.Objects.PATCH: get_all_patches(filter_deleted=filter_deleted),
        models.Objects.DELIVERABLE_TYPE: get_all_deliverable_types(filter_deleted=filter_deleted)
    }

    items = switch.get(model_type, lambda: None)

    if items is None:
        raise ObjectNotFoundError("There is no object of this type")
    else:
        return items


def get_page(sqlalchemy_query, page_number, model=None, order="newest"):
    page = 1
    try:
        page = int(page_number)
    except TypeError:
        pass

    try:
        if model:
            try:
                if order == "newest":
                    return sqlalchemy_query.order_by(
                        desc(model.time_created)
                    ).paginate(page).items
                else:
                    return sqlalchemy_query.order_by(
                        asc(model.time_created)
                    ).paginate(page).items
            except AttributeError:
                logging.warning("Could not sort model by creation_time".format(model))

        return sqlalchemy_query.paginate(page).items
    except Exception as e:
        # SQLAlchemy returns its own kind of http exception so we catch it
        if hasattr(e, "code"):
            if e.code == 404:
                raise ObjectNotFoundError
        else:
            raise



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

    return items[start:end]
