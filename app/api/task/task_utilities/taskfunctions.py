import logging

from sqlalchemy import desc, asc

from app import models, schemas
from flask import json
import hashlib
from app.api.task.task_utilities.task_socket_actions import ASSIGN_RIDER_TO_TASK, ASSIGN_COORDINATOR_TO_TASK
from app.exceptions import ObjectNotFoundError, SchemaValidationError


def roles_check_and_assign_user(task, user, role):
    if role == "rider":
        if "rider" not in user.roles:
            raise SchemaValidationError("Can not assign a non-rider as a rider")
        task.assigned_riders.append(user)
        socket_update_type = ASSIGN_RIDER_TO_TASK
    elif role == "coordinator":
        if "coordinator" not in user.roles:
            raise SchemaValidationError("Can not assign a non-coordinator as a coordinator")
        task.assigned_coordinators.append(user)
        socket_update_type = ASSIGN_COORDINATOR_TO_TASK
    else:
        raise SchemaValidationError("A role must be specified.")
    return socket_update_type


def get_uncompleted_tasks_query(query):
    return query.join(models.TasksParent).filter(
        models.TasksParent.relays.any(models.Task.time_dropped_off.is_(None)),
        models.Task.time_cancelled.is_(None),
        models.Task.time_rejected.is_(None)
    )


def get_items_before_parent(before_parent, page, order, query):
    if before_parent > 0:
        filtered_ordered_after = query.filter(models.Task.parent_id < before_parent)
    else:
        filtered_ordered_after = query

    if before_parent > 0 and filtered_ordered_after.count() == 0:
        raise ObjectNotFoundError
    if page > 0:
        if before_parent != 0:
            shift = (page * 20) - 20
            range = (before_parent - shift, before_parent - shift - 20)
            items = filtered_ordered_after.filter(
                models.Task.parent_id.between(range[1], range[0])
            ).all()
        else:
            items = get_tasks_page(filtered_ordered_after, page, order)
    else:
        items = filtered_ordered_after.all()

    return items


def get_tasks_page(sqlalchemy_query, page_number, order="newest"):
    model = models.Task
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
        raise

def get_filtered_query_by_status_non_relays(query, status):
    if status == "new":
        return query.filter(
            ~models.Task.assigned_riders.any(),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )

    elif status == "active":
        return query.filter(
            models.Task.assigned_riders.any(),
            ~models.Task.time_picked_up.isnot(None),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )

    elif status == "picked_up":
        return query.filter(
            models.Task.assigned_riders.any(),
            models.Task.time_picked_up.isnot(None),
            models.Task.time_dropped_off.is_(None),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )
    elif status == "delivered":
        return query.filter(
            models.Task.assigned_riders.any(),
            ~models.Task.time_dropped_off.is_(None),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )
    elif status == "cancelled":
        return query.filter(
            models.Task.time_cancelled.isnot(None),
            models.Task.time_rejected.is_(None)
        )
    elif status == "rejected":
        return query.filter(
            models.Task.time_rejected.isnot(None),
            models.Task.time_cancelled.is_(None)
        )
    else:
        return query



def get_filtered_query_by_status(query, status):
    if status == "new":
        return query.join(models.TasksParent).filter(
            ~models.TasksParent.relays.any(models.Task.assigned_riders.any()),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )

    elif status == "active":
        return query.join(models.TasksParent).filter(
            models.TasksParent.relays.any(models.Task.assigned_riders.any()),
            ~models.TasksParent.relays.any(models.Task.time_picked_up.isnot(None)),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )

    elif status == "picked_up":
        return query.join(models.TasksParent).filter(
            models.TasksParent.relays.any(models.Task.assigned_riders.any()),
            models.TasksParent.relays.any(models.Task.time_picked_up.isnot(None)),
            models.TasksParent.relays.any(models.Task.time_dropped_off.is_(None)),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )
    elif status == "delivered":
        return query.join(models.TasksParent).filter(
            models.TasksParent.relays.any(models.Task.assigned_riders.any()),
            ~models.TasksParent.relays.any(models.Task.time_dropped_off.is_(None)),
            models.Task.time_cancelled.is_(None),
            models.Task.time_rejected.is_(None)
        )
    elif status == "cancelled":
        return query.join(models.TasksParent).filter(
            models.Task.time_cancelled.isnot(None),
            models.Task.time_rejected.is_(None)
        )
    elif status == "rejected":
        return query.join(models.TasksParent).filter(
            models.Task.time_rejected.isnot(None),
            models.Task.time_cancelled.is_(None)
        )
    else:
        return query


def get_task_object(_id, with_deleted=False):
    if with_deleted:
        task = models.Task.query.with_deleted().filter_by(uuid=_id).first()
    else:
        task = models.Task.query.filter_by(uuid=_id).first()
    if not task:
        raise ObjectNotFoundError()
    return task


def set_previous_relay_uuids(task_parent):
    prev_task = None
    for i in sorted(task_parent.relays_with_deleted_cancelled_rejected, key=lambda t: t.order_in_relay):
        if i.deleted or i.time_cancelled or i.time_rejected:
            i.relay_previous_uuid = None
            continue
        if prev_task:
            i.relay_previous_uuid = prev_task.uuid
        else:
            i.relay_previous_uuid = None

        prev_task = i

    return task_parent


def get_task_parent_object(_id, with_deleted):
    if with_deleted:
        task_parent = models.TasksParent.query.with_deleted().filter_by(id=_id).first()
    else:
        task_parent = models.TasksParent.query.filter_by(id=_id).first()
    if not task_parent:
        raise ObjectNotFoundError()
    return task_parent


def get_all_tasks(filter_deleted=False):
    if filter_deleted:
        return models.Task.query.all()
    else:
        return models.Task.query.with_deleted().all()


def calculate_tasks_etag(data):
    tasks_schema = schemas.TaskSchema(many=True)
    json_data = json.dumps(tasks_schema.dump(data))
    return hashlib.sha1(bytes(json_data, 'utf-8')).hexdigest()


def calculate_task_etag(task_json):
    return hashlib.sha1(bytes(task_json, 'utf-8')).hexdigest()


