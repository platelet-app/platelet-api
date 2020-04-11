from flask import jsonify, request
from app import schemas, db, models, utilities
from flask_restplus import Resource
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

session_schema = schemas.SessionSchema()
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
            return jsonify(session_schema.dump(get_object(SESSION, session_id)).data)
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


@ns.route('/<session_id>/statistics',
          endpoint='session_statistics')
class SessionStatistics(Resource):
    @flask_praetorian.auth_required
    def get(self, session_id):
        session = get_object(SESSION, session_id)
        available_patches = get_all_objects(models.Objects.PATCH)
        available_priorities = get_all_objects(models.Objects.PRIORITY)
        tasks_plus_deleted = session.tasks.all()
        tasks = list(filter(lambda t: not t.flagged_for_deletion, tasks_plus_deleted))
        num_deleted = len(list(filter(lambda t: t.flagged_for_deletion, tasks_plus_deleted)))
        num_tasks = len(tasks)
        num_completed = len(list(filter(lambda t: t.time_dropped_off, tasks)))
        num_picked_up = len(list(filter(lambda t: t.time_picked_up and not t.time_dropped_off, tasks)))
        num_active = len(list(filter(lambda t: t.assigned_rider and not t.time_picked_up and not t.time_dropped_off, tasks)))
        num_rejected = len(list(filter(lambda t: t.time_rejected, tasks)))
        num_cancelled = len(list(filter(lambda t: t.time_cancelled, tasks)))
        num_unassigned = len(list(filter(lambda t: not t.assigned_rider, tasks)))

        riders_in_session = set(map(lambda t: t.rider, tasks))
        rider_counts = {}
        for rider in riders_in_session:
            if rider:
                riders_tasks = list(filter(lambda t: t.assigned_rider and rider.uuid == t.assigned_rider, tasks))
                rider_counts[rider.display_name] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, riders_tasks)))), available_priorities))
                rider_counts[rider.display_name]["Total"] = len(riders_tasks)
                rider_counts[rider.display_name]["None"] = len(list(filter(lambda t: not t.priority_id, riders_tasks)))
            else:
                unassigned_tasks = list(filter(lambda t: not t.assigned_rider, tasks))
                rider_counts["Unassigned"] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, unassigned_tasks)))), available_priorities))
                rider_counts["Unassigned"]["Total"] = len(unassigned_tasks)
                rider_counts["Unassigned"]["None"] = len(list(filter(lambda t: not t.priority_id, unassigned_tasks)))

        patches_in_session = set(map(lambda t: t.patch, tasks))
        patch_counts = {}
        for patch in patches_in_session:
            if patch:
                patch_tasks = list(filter(lambda t: t.patch and patch.id == t.patch_id, tasks))
                patch_counts[patch.label] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, patch_tasks)))), available_priorities))
                patch_counts[patch.label]["Total"] = len(patch_tasks)
                patch_counts[patch.label]["None"] = len(list(filter(lambda t: not t.patch_id, patch_tasks)))
            else:
                no_patch = list(filter(lambda t: not t.patch_id, tasks))
                patch_counts["None"] = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, no_patch)))), available_priorities))
                patch_counts["None"]["Total"] = len(no_patch)
                patch_counts["None"]["None"] = len(list(filter(lambda t: not t.priority_id, no_patch)))

        #rider_counts = dict(map(lambda rider: (rider.display_name if rider else "unassigned", len(list(filter(lambda t: not rider or t.assigned_rider == rider.uuid, tasks)))), riders_in_session))

        #patch_stats = dict(map(lambda patch: (patch.label, len(list(filter(lambda t: t.patch_id == patch.id, tasks)))), available_patches))
        priority_stats = dict(map(lambda priority: (priority.label, len(list(filter(lambda t: t.priority_id == priority.id, tasks)))), available_priorities))
        priority_stats["None"] = len(list(filter(lambda t: not t.priority_id, tasks)))

        last_changed_task = sorted(tasks_plus_deleted, key=lambda t: t.time_modified)
        time_active = str(round((last_changed_task[-1].time_modified - session.time_created).total_seconds()))

        return {"num_tasks": num_tasks,
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
            items = get_range(user.sessions.all(), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return sessions_schema.jsonify(items)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        calling_user = get_user_object_by_int_id(utilities.current_user_id()).uuid
        if request.get_json():
            try:
                session = load_request_into_object(SESSION)
                if session.user_uuid != str(calling_user):
                    if 'admin' not in utilities.current_rolenames():
                        return forbidden_error("only admins can create sessions for other users")
                    if not is_user_present(session.user_uuid):
                        return forbidden_error("cannot create a session for a non-existent user")
            except SchemaValidationError as e:
                return schema_validation_error(str(e))

        else:
            session = models.Session()
            session.user_uuid = calling_user

        db.session.add(session)
        db.session.commit()

        user_obj = get_user_object(session.user_uuid)

        return {'uuid': str(session.uuid), 'user_uuid': str(user_obj.uuid), 'message': 'Session {} created'.format(str(session.uuid))}, 201

