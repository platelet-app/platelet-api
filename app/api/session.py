from flask import jsonify, request
from app import schemas, db, models, utilities
from flask_restx import Resource, reqparse
import flask_praetorian
from flask_praetorian import utilities
from app import session_ns as ns
from app.exceptions import InvalidRangeError, ObjectNotFoundError, SchemaValidationError
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.userfunctions import get_user_object, is_user_present, get_user_object_by_int_id
from app.api.functions.sessionfunctions import session_id_match_or_admin
from app.api.functions.errors import forbidden_error, not_found, already_flagged_for_deletion_error, internal_error, schema_validation_error
from app.exceptions import AlreadyFlaggedForDeletionError
from app.utilities import get_object, get_range, get_all_objects
from app.utilities import add_item_to_delete_queue, remove_item_from_delete_queue

SESSION = models.Objects.SESSION
DELETE_FLAG = models.Objects.DELETE_FLAG

session_schema = schemas.SessionSchema(exclude=('tasks',))
sessions_schema = schemas.SessionSchema(many=True, exclude=('tasks',))

@ns.route('/<session_id>/restore', endpoint="session_undelete")
class SessionRestore(Resource):
    @flask_praetorian.roles_accepted("admin", "coordinator")
    def put(self, session_id):
        try:
            session = get_object(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        if session.flagged_for_deletion:
            # TODO: clean up from delete queue or let it clean up itself?
            delete_queue_session = get_object(DELETE_FLAG, session.uuid)
            for task in session.tasks:
                check = get_object(DELETE_FLAG, task.uuid)
                if check.time_created >= delete_queue_session.time_created and check.active:
                    remove_item_from_delete_queue(task)
            remove_item_from_delete_queue(session)

        else:
            return {'uuid': str(session.uuid), 'message': 'Session {} not flagged for deletion.'.format(session.uuid)}, 200
        return {'uuid': str(session.uuid), 'message': 'Session {} deletion flag removed.'.format(session.uuid)}, 200

@ns.route('/<session_id>',
          endpoint='session_detail')
class Session(Resource):
    @flask_praetorian.auth_required
    def get(self, session_id):
        try:
            session = get_object(SESSION, session_id)
            session.is_owner = utilities.current_user().uuid == session.coordinator_uuid
            return session_schema.dump(session)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    @session_id_match_or_admin
    def delete(self, session_id):
        try:
            session = get_object(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        try:
            add_item_to_delete_queue(session)

            for i in session.tasks:
                try:
                    add_item_to_delete_queue(i)
                except AlreadyFlaggedForDeletionError:
                    continue

        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(SESSION, str(session.uuid))

        return {'uuid': str(session.uuid), 'message': "Session queued for deletion"}, 202

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    @session_id_match_or_admin
    def put(self, session_id):
        try:
            session = get_object(SESSION, session_id)
            if session.flagged_for_deletion:
                return not_found(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        load_request_into_object(SESSION, instance=session)
        db.session.commit()
        return {'uuid': str(session.uuid), 'message': 'Session {} updated.'.format(session.uuid)}, 200

@ns.route(
    '/<session_id>/assign_collaborator',
    endpoint="sessions_assign_collaborator")
class UserCollaborators(Resource):
    @flask_praetorian.roles_accepted('admin', 'coordinator')
    @session_id_match_or_admin
    def put(self, session_id):
        try:
            session = get_object(SESSION, session_id)
            if session.flagged_for_deletion:
                return not_found(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        #load_request_into_object(TASK, instance=task)

        parser = reqparse.RequestParser()
        parser.add_argument('user_uuid')
        args = parser.parse_args()
        user_uuid = args['user_uuid']
        try:
            user = get_object(models.Objects.USER, user_uuid)
            if user.flagged_for_deletion:
                return not_found(models.Objects.USER, user_uuid)
        except ObjectNotFoundError:
            return not_found(models.Objects.USER, user_uuid)

        if "coordinator" not in user.roles:
            return forbidden_error("Can not assign a non-coordinator as a collaborator.", user_uuid)

        if user.uuid in [u.uuid for u in session.collaborators]:
            return forbidden_error("Can not add a collaborator twice.")

        session.collaborators.append(user)
        db.session.add(session)
        db.session.commit()
        return {'uuid': str(session.uuid), 'message': 'Session {} updated.'.format(session.uuid)}, 200


@ns.route('/<session_id>/statistics',
          endpoint='session_statistics')
class SessionStatistics(Resource):
    @flask_praetorian.auth_required
    def get(self, session_id):
        if not session_id:
            return not_found(SESSION)
        try:
            session = get_object(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)
        available_priorities = get_all_objects(models.Objects.PRIORITY)
        tasks_plus_deleted = session.tasks.all()
        tasks = list(filter(lambda t: not t.flagged_for_deletion, tasks_plus_deleted))
        num_deleted = len(list(filter(lambda t: t.flagged_for_deletion, tasks_plus_deleted)))
        num_tasks = len(tasks)
        # tasks with time_dropped_off set
        num_completed = len(list(filter(lambda t: t.time_dropped_off, tasks)))
        # tasks with time_picked_up set and not time_dropped_off
        num_picked_up = len(list(filter(lambda t: t.time_picked_up and not t.time_dropped_off, tasks)))
        # tasks that only have an assigned rider
        num_active = len(list(filter(lambda t: t.assigned_users and not t.time_picked_up and not t.time_dropped_off, tasks)))
        # tasks with time_rejected set
        num_rejected = len(list(filter(lambda t: t.time_rejected, tasks)))
        # tasks with time_cancelled set
        num_cancelled = len(list(filter(lambda t: t.time_cancelled, tasks)))
        # tasks with no assigned rider
        num_unassigned = len(list(filter(lambda t: not t.assigned_users, tasks)))

        # unique list of all riders that are assigned in this session
        #TODO: update for multiple assigned riders

        riders_in_session = set()
        for task in tasks:
            riders_in_session = riders_in_session | set(map(lambda user: user, task.assigned_users))
            riders_in_session = riders_in_session | {None}

        rider_counts = {}
        num_all_riders = 0
        for rider in riders_in_session:
            if rider:
                # get the tasks for a rider
                riders_tasks = list()
                for task in tasks:
                    task_users = map(lambda u: u.uuid, task.assigned_users)
                    if rider.uuid in task_users:
                        riders_tasks.append(task)
                num_all_riders += len(riders_tasks)
                # match the tasks with all priorities that are available and return a dictionary: prioritylabel: numtasks.
                rider_counts[rider.display_name] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, riders_tasks)))), available_priorities))
                # total number of tasks for that rider
                rider_counts[rider.display_name]["Total"] = len(riders_tasks)
                # number of tasks for that rider with no priority
                rider_counts[rider.display_name]["None"] = len(list(filter(lambda t: not t.priority_id, riders_tasks)))
            else:
                # same as above but for tasks that are unassigned
                unassigned_tasks = list(filter(lambda t: not t.assigned_users, tasks))
                rider_counts["Unassigned"] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, unassigned_tasks)))), available_priorities))
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
                patch_counts[patch.label] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, patch_tasks)))), available_priorities))
                # total number of tasks for that patch
                patch_counts[patch.label]["Total"] = len(patch_tasks)
                # total number of tasks with no priority
                patch_counts[patch.label]["None"] = len(list(filter(lambda t: not t.priority_id, patch_tasks)))
            else:
                # same as above but for tasks with no patch
                no_patch = list(filter(lambda t: not t.patch_id, tasks))
                patch_counts["None"] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, no_patch)))), available_priorities))
                patch_counts["None"]["Total"] = len(no_patch)
                patch_counts["None"]["None"] = len(list(filter(lambda t: not t.priority_id, no_patch)))

        # priority totals
        priority_stats = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, tasks)))), available_priorities))
        priority_stats["None"] = len(list(filter(lambda t: not t.priority_id, tasks)))

        # get the task that was last modified on this session
        last_changed_task = sorted(tasks_plus_deleted, key=lambda t: t.time_modified)
        if last_changed_task:
            # calculate the time between the last modified task and the session creation date
            time_active = str(round((last_changed_task[-1].time_modified - session.time_created).total_seconds()))
        else:
            # if no tasks then the time between the session creation date and session modification date
            time_active = str(round((session.time_modified - session.time_created).total_seconds()))

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


@ns.route(
    's',
    's/<user_id>',
    's/<user_id>/<_range>',
    's/<user_id>/<_range>/<order>',
    endpoint='sessions_list')
class Sessions(Resource):
    @flask_praetorian.auth_required
    def get(self, user_id, _range=None, order="descending"):
        try:
            user = get_user_object(user_id)
        except ObjectNotFoundError:
            return not_found(models.Objects.USER, user_id)

        try:
            items = set(get_range(user.sessions.all() + user.collaborator_sessions, _range, order))
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        for i in items:
            i.is_owner = utilities.current_user().uuid == i.coordinator_uuid

        return sessions_schema.jsonify(items)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        calling_user = utilities.current_user().uuid
        if request.get_json():
            try:
                session = load_request_into_object(SESSION)
                if session.coordinator_uuid != str(calling_user):
                    if 'admin' not in utilities.current_rolenames():
                        return forbidden_error("only admins can create sessions for other users")
                    if not is_user_present(session.coordinator_uuid):
                        return forbidden_error("cannot create a session for a non-existent user")
            except SchemaValidationError as e:
                return schema_validation_error(str(e))

        else:
            session = models.Session()
            session.coordinator_uuid = calling_user

        db.session.add(session)
        db.session.commit()

        user_obj = get_user_object(session.coordinator_uuid)

        return {'uuid': str(session.uuid), 'coordinator_uuid': str(user_obj.uuid), 'message': 'Session {} created'.format(str(session.uuid))}, 201

