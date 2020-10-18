from flask import jsonify, request
from flask_socketio import emit
from marshmallow import ValidationError
from sqlalchemy import exists

from app import schemas, models, socketio
from flask_restx import Resource, reqparse
import flask_praetorian
from app import task_ns as ns
from app.api.task.task_utilities.taskfunctions import emit_socket_broadcast
from app.utilities import add_item_to_delete_queue, remove_item_from_delete_queue, get_unspecified_object, get_page, \
    get_query
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
            if task.relay_previous_uuid:
                task.relay_previous_uuid = None
                db.session.commit()
            for deliverable in task.deliverables:
                if not deliverable.flagged_for_deletion:
                    add_item_to_delete_queue(deliverable)
        except AlreadyFlaggedForDeletionError:
            return {'uuid': str(task.uuid), 'message': "Task queued for deletion"}, 202

        return {'uuid': str(task.uuid), 'message': "Task queued for deletion"}, 202

    @flask_praetorian.auth_required
    @check_rider_match
    # @check_parent_or_collaborator_or_admin_match
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
        parser = reqparse.RequestParser()
        parser.add_argument("role", type=str, location="args")
        args = parser.parse_args()
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)
        if args['role'] == "rider":
            return assigned_users_schema.dump(task.assigned_riders)
        elif args['role'] == "coordinator":
            return assigned_users_schema.dump(task.assigned_coordinators)
        else:
            combined = []
            combined.extend(task.assigned_coordinators)
            combined.extend(task.assigned_riders)
            return assigned_users_schema.dump(combined)

    @flask_praetorian.roles_accepted('admin', 'coordinator', 'rider')
    # @check_parent_or_collaborator_or_admin_match
    def put(self, task_id):
        try:
            task = get_object(TASK, task_id)
            if task.flagged_for_deletion:
                return not_found(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        parser = reqparse.RequestParser()
        parser.add_argument("role", type=str, location="args")
        parser.add_argument('user_uuid')
        args = parser.parse_args()
        user_uuid = args['user_uuid']
        try:
            user = get_object(models.Objects.USER, user_uuid)
            if user.flagged_for_deletion:
                return not_found(models.Objects.USER, user_uuid)
        except ObjectNotFoundError:
            return not_found(models.Objects.USER, user_uuid)

        if args['role'] == "rider":
            if "rider" not in user.roles:
                return forbidden_error("Can not assign a non-rider as a rider.", user_uuid)

            task.assigned_riders.append(user)

        elif args['role'] == "coordinator":
            if "coordinator" not in user.roles:
                return forbidden_error("Can not assign a non-coordinator as a coordinator.", user_uuid)
            task.assigned_coordinators.append(user)

        else:
            return forbidden_error("Type of role must be specified.", task_id)

        db.session.add(task)
        db.session.commit()
        request_json = request.get_json()
        emit_socket_broadcast(request_json, task_id, "assign_user")
        return {'uuid': str(task.uuid), 'message': 'Task {} updated.'.format(task.uuid)}, 200

    @flask_praetorian.roles_accepted('admin', 'coordinator', 'rider')
    # @check_parent_or_collaborator_or_admin_match
    def delete(self, task_id):
        try:
            task = get_object(TASK, task_id)
            if task.flagged_for_deletion:
                return not_found(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        parser = reqparse.RequestParser()
        parser.add_argument('user_uuid')
        parser.add_argument("role", type=str, location="args")
        args = parser.parse_args()
        user_uuid = args['user_uuid']
        try:
            user = get_object(models.Objects.USER, user_uuid)
            if user.flagged_for_deletion:
                return not_found(models.Objects.USER, user_uuid)
        except ObjectNotFoundError:
            return not_found(models.Objects.USER, user_uuid)

        if args['role'] == "rider":
            filtered_riders = list(filter(lambda u: u.uuid != user.uuid, task.assigned_riders))
            task.assigned_riders = filtered_riders

        elif args['role'] == "coordinator":
            filtered_coordinators = list(filter(lambda u: u.uuid != user.uuid, task.assigned_coordinators))
            task.assigned_riders = filtered_coordinators
        else:
            return forbidden_error("Type of role must be specified.", task_id)

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
        query = get_query(TASK)
        # filter deleted tasks and relays
        query_filtered = query.filter(
            models.Task.flagged_for_deletion.is_(False),
            models.Task.relay_previous_uuid.is_(None))
        items = get_page(query_filtered, page, order=order, model=models.Task)
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
        return {'uuid': str(task.uuid), 'time_created': str(task.time_created),
                'message': 'Task {} created'.format(task.uuid)}, 201


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
            parser.add_argument("status", type=str, location="args")
            args = parser.parse_args()
            page = args['page'] if args['page'] else 1
            role = args['role']
            status = args['status']
            order = args['order'] if args['order'] else "descending"
            if role == "rider":
                query = requested_user.tasks_as_rider
            elif role == "coordinator":
                query = requested_user.tasks_as_coordinator
            elif role == "author":
                query = requested_user.tasks_as_author
            else:
                query = requested_user.tasks_as_coordinator

            # filter deleted tasks and relays
            query_deleted = query.filter(
                models.Task.flagged_for_deletion.is_(False),
                models.Task.relay_previous_uuid.is_(None))

            if status == "new":
                filtered = query_deleted.filter(
                    models.Task.time_cancelled.is_(None),
                    models.Task.time_rejected.is_(None),
                ).filter(~models.Task.assigned_riders.any())
            elif status == "active":
                filtered = query_deleted.filter(
                    models.Task.time_picked_up.is_(None),
                    models.Task.time_dropped_off.is_(None),
                    models.Task.time_cancelled.is_(None),
                    models.Task.time_rejected.is_(None),
                ).filter(models.Task.assigned_riders.any())
            elif status == "picked_up":
                filtered = query_deleted.filter(
                    models.Task.time_picked_up.isnot(None),
                    models.Task.time_dropped_off.is_(None),
                    models.Task.time_cancelled.is_(None),
                    models.Task.time_rejected.is_(None)
                ).filter(models.Task.assigned_riders.any())
            # TODO: this needs to account for relays
            elif status == "delivered":
                filtered = query_deleted.filter(
                    models.Task.time_dropped_off.isnot(None),
                    models.Task.time_dropped_off.isnot(None),
                    models.Task.time_cancelled.is_(None),
                    models.Task.time_rejected.is_(None)
                ).filter(models.Task.assigned_riders.any())
            elif status == "cancelled":
                filtered = query_deleted.filter(models.Task.time_cancelled.isnot(None))
            elif status == "rejected":
                filtered = query_deleted.filter(models.Task.time_rejected.isnot(None))
            else:
                filtered = query_deleted

            items = get_page(filtered, page, order=order, model=models.Task)
        except ObjectNotFoundError:
            return not_found(TASK)
        except Exception as e:
            return internal_error(e)

        return tasks_schema.dump(items)
