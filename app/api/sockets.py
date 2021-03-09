import json

from flask_praetorian.utilities import current_guard
from uuid import UUID

from flask_socketio import emit, join_room, leave_room, SocketIO
from sqlalchemy import union_all

from app import models, schemas, app
from app import api_version
from threading import Lock

from app.api.functions.utilities import get_object
from app.api.task.task_utilities.task_socket_actions import TASKS_REFRESH, TASK_ASSIGNMENTS_REFRESH
from app.api.task.task_utilities.taskfunctions import get_uncompleted_tasks_query
from app.exceptions import ObjectNotFoundError

thread = None
thread_lock = Lock()

TASK = models.Objects.TASK
USER = models.Objects.USER
task_schema = schemas.TaskSchema(exclude=("comments",))
tasks_schema = schemas.TaskSchema(many=True, exclude=("comments",))


class AuthenticatedSocketConnection:
    def __init__(self):
        namespace_tasks = "/api/{}/subscribe".format(api_version)
        namespace_comments = "/api/{}/subscribe_comments".format(api_version)
        namespace_assignments = "/api/{}/subscribe_assignments".format(api_version)
        self.authenticated = False
        if app.config['CORS_ENABLED']:
            self.socketIO = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGIN'].split(","), message_queue=app.config['REDIS_URL'])
        else:
            self.socketIO = SocketIO(app, message_queue=app.config['REDIS_URL'])
        self.socketIO.on_event("refresh_task_data", self.check_etags, namespace=namespace_tasks)
        self.socketIO.on_event('refresh_task_assignments', self.check_assignments, namespace=namespace_tasks)
        self.socketIO.on_event('subscribe', self.subscribe_to_object, namespace=namespace_tasks)
        self.socketIO.on_event('unsubscribe', self.unsubscribe_from_object, namespace=namespace_tasks)
        self.socketIO.on_event('subscribe_many', self.subscribe_to_objects, namespace=namespace_tasks)
        self.socketIO.on_event('unsubscribe_many', self.unsubscribe_from_objects, namespace=namespace_tasks)

        self.socketIO.on_event('subscribe', self.subscribe_to_comments, namespace=namespace_comments)
        self.socketIO.on_event('unsubscribe', self.unsubscribe_from_comments, namespace=namespace_comments)
        self.socketIO.on_event('subscribe_coordinator', self.subscribe_to_coordinator_assignments,
                               namespace=namespace_assignments)
        self.socketIO.on_event('subscribe_rider', self.subscribe_to_rider_assignments, namespace=namespace_assignments)
        self.socketIO.on_event('unsubscribe_coordinator', self.unsubscribe_from_coordinator_assignments,
                               namespace=namespace_assignments)
        self.socketIO.on_event('unsubscribe_rider', self.unsubscribe_from_rider_assignments,
                               namespace=namespace_assignments)

        self.socketIO.on_event('authenticate', self.authenticate, namespace=namespace_tasks)
        self.socketIO.on_event('authenticate', self.authenticate, namespace=namespace_comments)
        self.socketIO.on_event('authenticate', self.authenticate, namespace=namespace_assignments)

        self.user_uuid = None

    def authenticate(self, token):
        guard = current_guard()
        try:
            jwt_data = guard.extract_jwt_token(token)
            user_id = jwt_data.get('id')
            user = guard.user_class.identify(user_id)
            self.user_uuid = user.uuid
            self.authenticated = True
            emit("auth_response", {"auth_status": True, "message": "Authentication successful"})
        except Exception as e:
            emit("auth_response", {"auth_status": False, "message": "Authentication failed. Reason: {}".format(str(e))})

    def check_etags(self, uuid_etag_dict):
        if not self.authenticated:
            return False
        result = []
        if uuid_etag_dict:
            for entry, etag in uuid_etag_dict.items():
                try:
                    task = get_object(TASK, entry)
                    dump = task_schema.dump(task)
                    if dump['etag'] != etag:
                        result.append(dump)
                except ObjectNotFoundError:
                    result.append({"uuid": entry, "deleted": True})
        else:
            print("Empty uuid etag dict received")
        emit('request_response', {
            'data': json.dumps(result),
            'type': TASKS_REFRESH
        })

    def check_assignments(self, user_uuid, task_uuids, role):
        if not self.authenticated:
            return False
        user = get_object(USER, user_uuid)
        if role == "coordinator":
            query = user.tasks_as_coordinator
        elif role == "rider":
            query = user.tasks_as_rider
        else:
            query = union_all(user.tasks_as_rider, user.tasks_as_coordinator)

        task_uuids_converted = [UUID(t) for t in task_uuids]

        active_query = get_uncompleted_tasks_query(query)

        active_deleted_query = active_query.filter(models.Task.deleted.is_(False))

        q = active_deleted_query.filter(~models.Task.uuid.in_(task_uuids_converted))

        emit('request_response', {
            'data': tasks_schema.dump(q.all()),
            'type': TASK_ASSIGNMENTS_REFRESH
        })

    def subscribe_to_object(self, obj_uuid):
        if not self.authenticated:
            return False
        join_room(obj_uuid)
        emit('response', {'data': "Subscribed to object with uuid {}.".format(obj_uuid)})

    def subscribe_to_objects(self, uuids_list):
        if not self.authenticated:
            return False
        for i in uuids_list:
            join_room(i)
        emit('response', {'data': "Subscribed to {} objects".format(len(uuids_list))})

    def unsubscribe_from_objects(self, uuids_list):
        for i in uuids_list:
            leave_room(i)
        emit('response', {'data': "Unsubscribed from {} objects".format(len(uuids_list))})

    def unsubscribe_from_object(self, obj_uuid):
        leave_room(obj_uuid)
        emit('response', {'data': "Unsubscribed from object with uuid {}.".format(obj_uuid)})

    def subscribe_to_comments(self, obj_uuid):
        if not self.authenticated:
            return False
        join_room(obj_uuid)
        emit('response', {'data': "Subscribed to comments for object with uuid {}.".format(obj_uuid)})

    def unsubscribe_from_comments(self, obj_uuid):
        leave_room(obj_uuid)
        emit('response', {'data': "Unsubscribed from comments for object with uuid {}.".format(obj_uuid)})

    def subscribe_to_coordinator_assignments(self, user_uuid):
        if not self.authenticated:
            return False
        join_room("{}_coordinator".format(user_uuid))
        emit('response', {'data': "Subscribed to coordinator assignments for user with uuid {}.".format(user_uuid)})

    def subscribe_to_rider_assignments(self, user_uuid):
        if not self.authenticated:
            return False
        join_room("{}_rider".format(user_uuid))
        emit('response', {'data': "Subscribed to rider assignments for user with uuid {}.".format(user_uuid)})

    def unsubscribe_from_coordinator_assignments(self, user_uuid):
        leave_room("{}_coordinator".format(user_uuid))
        emit('response', {'data': "Unsubscribed from coordinator assignments for user with uuid {}.".format(user_uuid)})

    def unsubscribe_from_rider_assignments(self, user_uuid):
        leave_room("{}_rider".format(user_uuid))
        emit('response', {'data': "Unsubscribed from rider assignments for user with uuid {}.".format(user_uuid)})


socketio = AuthenticatedSocketConnection()
