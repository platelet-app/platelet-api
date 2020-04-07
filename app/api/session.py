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
from app.utilities import get_object, get_range
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
            session = get_object(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        return jsonify(session_schema.dump(session).data)

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
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        load_request_into_object(SESSION, instance=session)
        db.session.commit()
        return {'uuid': str(session.uuid), 'message': 'Session {} updated.'.format(session.uuid)}, 200


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

