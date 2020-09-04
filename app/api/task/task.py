from flask import jsonify, request
from flask_socketio import emit
from marshmallow import ValidationError

from app import schemas, models, socketio
from flask_restx import Resource, reqparse
import flask_praetorian
from app import task_ns as ns
from app.api.task.task_utilities.taskfunctions import emit_socket_broadcast
from app.utilities import add_item_to_delete_queue, remove_item_from_delete_queue, get_unspecified_object, get_page
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
    #@check_parent_or_collaborator_or_admin_match
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

        request_json = request.get_json()
        emit_socket_broadcast(request_json, task_id, "update")
        db.session.commit()
        return {'uuid': str(task.uuid), 'message': "Task {} updated.".format(task.uuid)}


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

    @flask_praetorian.roles_accepted('admin', 'coordinator', 'rider')
    #@check_parent_or_collaborator_or_admin_match
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
        request_json = request.get_json()
        emit_socket_broadcast(request_json, task_id, "assign_user")
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200

    @flask_praetorian.roles_accepted('admin', 'coordinator', 'rider')
    #@check_parent_or_collaborator_or_admin_match
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
        request_json = request.get_json()
        emit_socket_broadcast(request_json, task_id, "remove_assigned_user")
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200


@ns.route('s',
          endpoint="tasks_list_all")
class Tasks(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", type=int, location="args")
        parser.add_argument("role", type=str, location="args")
        parser.add_argument("order", type=str, location="args")
        args = parser.parse_args()
        page = args['page'] if args['page'] else 1
        order = args['order'] if args['order'] else "newest"
        items = get_page(models.Task.query, page, order=order, model=models.Task)
        return tasks_schema.dump(items)

    @flask_praetorian.auth_required
    def post(self):
        try:
            task = load_request_into_object(TASK)
        except SchemaValidationError as e:
            return schema_validation_error(str(e))
        task.author_uuid = utilities.current_user().uuid
        db.session.add(task)
        db.session.commit()
        return {'uuid': str(task.uuid), 'time_created': str(task.time_created), 'message': 'Task {} created'.format(task.uuid)}, 201


@ns.route('s/<user_uuid>',
          endpoint="tasks_list")
class Tasks(Resource):
    @flask_praetorian.auth_required
    def get(self, user_uuid):
        if not user_uuid:
            return not_found(models.Objects.USER)
        try:
            requested_user = get_object(models.Objects.USER, user_uuid)
            if not requested_user:
                return not_found(models.Objects.USER, user_uuid)
            if requested_user.flagged_for_deletion:
                return not_found(requested_user.object_type, user_uuid)
        except ObjectNotFoundError:
            return not_found(models.Objects.USER, user_uuid)
        try:
            # TODO: add page size querystring
            parser = reqparse.RequestParser()
            parser.add_argument("page", type=int, location="args")
            parser.add_argument("role", type=str, location="args")
            parser.add_argument("order", type=str, location="args")
            args = parser.parse_args()
            page = args['page'] if args['page'] else 1
            role = args['role']
            order = args['order'] if args['order'] else "descending"
            if role == "rider":
                items = get_page(requested_user.tasks_as_rider, page, order=order, model=models.Task)
            elif role == "coordinator":
                items = get_page(requested_user.tasks_as_coordinator, page, order=order, model=models.Task)
            else:
                # TODO: this messes up pagination figure out how to do it with sqlalchemy
                items = get_page(requested_user.tasks_as_rider, page, order=order, model=models.Task)
                items.extend(get_page(requested_user.tasks_as_coordinator, page, order=order, model=models.Task))
                items.sort(key=lambda t: t.time_created)
                items = items[0:20]
        except Exception as e:
            return internal_error(e)

        return tasks_schema.dump(items)
