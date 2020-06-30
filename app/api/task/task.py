from flask import jsonify
from marshmallow import ValidationError

from app import schemas, models
from flask_restx import Resource, reqparse
import flask_praetorian
from app import task_ns as ns
from app.utilities import add_item_to_delete_queue, remove_item_from_delete_queue, get_unspecified_object
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import internal_error, not_found, forbidden_error, schema_validation_error, \
    already_flagged_for_deletion_error
from app.exceptions import ObjectNotFoundError, InvalidRangeError, SchemaValidationError, AlreadyFlaggedForDeletionError
from app.api.task.task_utilities.decorators import check_rider_match, check_parent_or_collaborator_or_admin_match
from app.utilities import get_object, get_range
from flask_praetorian import utilities

from app import db

task_schema = schemas.TaskSchema()
tasks_schema = schemas.TaskSchema(many=True)
#assigned_users_schema = schemas.AssignedUsersSchema(many=True)
assigned_users_schema = schemas.UserSchema(many=True)

TASK = models.Objects.TASK
SESSION = models.Objects.SESSION
DELETE_FLAG = models.Objects.DELETE_FLAG

@ns.route('/<task_id>/restore', endpoint="task_undelete")
class TaskRestore(Resource):
    @flask_praetorian.roles_accepted("admin", "coordinator")
    def put(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        if task.flagged_for_deletion:
            delete_queue_task = get_object(DELETE_FLAG, task.uuid)
            for deliverable in task.deliverables:
                check = get_object(DELETE_FLAG, deliverable.uuid)
                if check.time_created >= delete_queue_task.time_created and check.active:
                    remove_item_from_delete_queue(deliverable)
            remove_item_from_delete_queue(task)
        else:
            return {'uuid': str(task.uuid), 'message': 'Task {} not flagged for deletion.'.format(task.uuid)}, 200
        return {'uuid': str(task.uuid), 'message': 'Task {} deletion flag removed.'.format(task.uuid)}, 200

@ns.route('/<task_id>', endpoint="task_detail")
class Task(Resource):
    @flask_praetorian.auth_required
    def get(self, task_id):
        try:
            return jsonify(task_schema.dump(get_object(TASK, task_id)))
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    def delete(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)
        try:
            add_item_to_delete_queue(task)
            for deliverable in task.deliverables:
                if not deliverable.flagged_for_deletion:
                    add_item_to_delete_queue(deliverable)
        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(TASK, str(task.uuid))

        return {'uuid': str(task.uuid), 'message': "Task queued for deletion"}, 202

    @flask_praetorian.auth_required
    @check_rider_match
    @check_parent_or_collaborator_or_admin_match
    def put(self, task_id):
        try:
            task = get_object(TASK, task_id)
            if task.flagged_for_deletion:
                return not_found(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        try:
            load_request_into_object(TASK, instance=task)
        except ValidationError as e:
            return schema_validation_error(e)

        db.session.commit()
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200

# TODO: make this do checks for the calling users
@ns.route(
    '/<task_id>/assigned_users',
    endpoint="tasks_assign_user")
class TasksAssignees(Resource):
    @flask_praetorian.auth_required
    def get(self, task_id):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)
        return assigned_users_schema.dump(task.assigned_users)

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    @check_parent_or_collaborator_or_admin_match
    def put(self, task_id):
        try:
            task = get_object(TASK, task_id)
            if task.flagged_for_deletion:
                return not_found(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

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

        if "rider" not in user.roles:
            return forbidden_error("Can not assign a non-rider as an assignee.", user_uuid)

        task.assigned_users.append(user)
        db.session.add(task)
        db.session.commit()
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    @check_parent_or_collaborator_or_admin_match
    def delete(self, task_id):
        try:
            task = get_object(TASK, task_id)
            if task.flagged_for_deletion:
                return not_found(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

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

        filtered_assignees = list(filter(lambda u: u.uuid != user.uuid, task.assigned_users))

        task.assigned_users = filtered_assignees
        db.session.add(task)
        db.session.commit()
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200


@ns.route('s',
          's/<session_user_id>',
          endpoint="tasks_list")
class Tasks(Resource):
    @flask_praetorian.auth_required
    def get(self, session_user_id, _range=None, order="ascending"):
        if not session_user_id:
            return not_found(models.Objects.UNKNOWN)
        try:
            session_user = get_unspecified_object(session_user_id)
            if not session_user:
                return not_found(models.Objects.UNKNOWN, session_user_id)
            if session_user.flagged_for_deletion:
                return not_found(session_user.object_type, session_user_id)
        except ObjectNotFoundError:
            return not_found(models.Objects.UNKNOWN, session_user_id)
        try:
            items = get_range(session_user.tasks.all(), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return tasks_schema.dump(items)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        try:
            task = load_request_into_object(TASK)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))
        session = get_object(SESSION, task.session_uuid)
        calling_user = utilities.current_user()
        if calling_user.uuid in [u.uuid for u in session.collaborators] or calling_user.uuid == session.coordinator_uuid:
            db.session.add(task)
            db.session.commit()
            return {'uuid': str(task.uuid), 'time_created': str(task.time_created), 'message': 'Task {} created'.format(task.uuid)}, 201
        else:
            return forbidden_error("You do not have permission to post new tasks on this session.", str(session.uuid))
