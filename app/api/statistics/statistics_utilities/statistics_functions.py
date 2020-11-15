from app import models
from app.api.functions.utilities import get_all_objects


def generate_statistics_from_tasks(tasks):
    available_priorities = get_all_objects(models.Objects.PRIORITY)
    tasks_plus_deleted = tasks
    tasks = list(filter(lambda t: not t.deleted, tasks_plus_deleted))
    num_deleted = len(list(filter(lambda t: t.deleted, tasks_plus_deleted)))
    num_tasks = len(tasks)
    # tasks with time_dropped_off set
    num_completed = len(list(filter(lambda t: t.time_dropped_off, tasks)))
    # tasks with time_picked_up set and not time_dropped_off
    num_picked_up = len(list(filter(lambda t: t.time_picked_up and not t.time_dropped_off, tasks)))
    # tasks that only have an assigned rider
    num_active = len(
        list(filter(lambda t: t.assigned_riders and not t.time_picked_up and not t.time_dropped_off, tasks)))
    # tasks with time_rejected set
    num_rejected = len(list(filter(lambda t: t.time_rejected, tasks)))
    # tasks with time_cancelled set
    num_cancelled = len(list(filter(lambda t: t.time_cancelled, tasks)))
    # tasks with no assigned rider
    num_unassigned = len(list(filter(lambda t: not t.assigned_riders, tasks)))

    # unique list of all riders that are assigned in this session
    # TODO: update for multiple assigned riders

    riders_in_session = set()
    for task in tasks:
        riders_in_session = riders_in_session | set(map(lambda user: user, task.assigned_riders))
        riders_in_session = riders_in_session | {None}

    rider_counts = {}
    num_all_riders = 0
    for rider in riders_in_session:
        if rider:
            # get the tasks for a rider
            riders_tasks = list()
            for task in tasks:
                task_users = map(lambda u: u.uuid, task.assigned_riders)
                if rider.uuid in task_users:
                    riders_tasks.append(task)
            num_all_riders += len(riders_tasks)
            # match the tasks with all priorities that are available and return a dictionary: prioritylabel: numtasks.
            rider_counts[rider.display_name] = dict(map(lambda priority: (
                priority.label, len(list(filter(lambda t: t.priority_id == priority.id, riders_tasks)))),
                                                        available_priorities))
            # total number of tasks for that rider
            rider_counts[rider.display_name]["Total"] = len(riders_tasks)
            # number of tasks for that rider with no priority
            rider_counts[rider.display_name]["None"] = len(list(filter(lambda t: not t.priority_id, riders_tasks)))
        else:
            # same as above but for tasks that are unassigned
            unassigned_tasks = list(filter(lambda t: not t.assigned_riders, tasks))
            rider_counts["Unassigned"] = dict(map(lambda priority: (
                priority.label, len(list(filter(lambda t: t.priority_id == priority.id, unassigned_tasks)))),
                                                  available_priorities))
            rider_counts["Unassigned"]["Total"] = len(unassigned_tasks)
            rider_counts["Unassigned"]["None"] = len(list(filter(lambda t: not t.priority_id, unassigned_tasks)))
            num_all_riders += len(unassigned_tasks)

    # unique list of all the patches that are set in this session
    patches_in_session = set(map(lambda t: t.patch, tasks))
    patch_counts = {}
    for patch in patches_in_session:
        if patch:
            # get all tasks for a certain patch
            patch_tasks = list(filter(lambda t: t.patch and patch.id == t.patch_id, tasks))
            # match the tasks with all priorities that are available and return a dictionary: prioritylabel: numtasks.
            patch_counts[patch.label] = dict(map(lambda priority: (
                priority.label, len(list(filter(lambda t: t.priority_id == priority.id, patch_tasks)))),
                                                 available_priorities))
            # total number of tasks for that patch
            patch_counts[patch.label]["Total"] = len(patch_tasks)
            # total number of tasks with no priority
            patch_counts[patch.label]["None"] = len(list(filter(lambda t: not t.priority_id, patch_tasks)))
        else:
            # same as above but for tasks with no patch
            no_patch = list(filter(lambda t: not t.patch_id, tasks))
            patch_counts["None"] = dict(map(
                lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, no_patch)))),
                available_priorities))
            patch_counts["None"]["Total"] = len(no_patch)
            patch_counts["None"]["None"] = len(list(filter(lambda t: not t.priority_id, no_patch)))

    # priority totals
    priority_stats = dict(
        map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, tasks)))),
            available_priorities))
    priority_stats["None"] = len(list(filter(lambda t: not t.priority_id, tasks)))

    # get the task that was last modified on this session
    last_changed_task = sorted(tasks_plus_deleted, key=lambda t: t.time_modified)[-1]
    first_created_task = sorted(tasks_plus_deleted, key=lambda t: t.time_created)[0]
    time_active = None
    if last_changed_task and first_created_task:
        # calculate the time between the last modified task and the first created task
        time_active = str(round((last_changed_task.time_modified - first_created_task.time_created).total_seconds()))

    return {"num_tasks": num_tasks,
            "num_all_riders": num_all_riders,
            "num_deleted": num_deleted,
            "num_completed": num_completed,
            "num_picked_up": num_picked_up,
            "num_active": num_active,
            "num_unassigned": num_unassigned,
            "num_rejected": num_rejected,
            "num_cancelled": num_cancelled,
            "patches": patch_counts,
            "riders": rider_counts,
            "priorities": priority_stats,
            "time_active": time_active}, 200
