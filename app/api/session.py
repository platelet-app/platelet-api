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
from app.api.functions.errors import forbidden_error, not_found, unauthorised_error, internal_error, schema_validation_error
from app.utilities import get_object, get_range
from app.utilities import add_item_to_delete_queue

SESSION = models.Objects.SESSION

session_schema = schemas.SessionSchema()
sessions_schema = schemas.SessionSchema(many=True, exclude=('tasks',))


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

        return add_item_to_delete_queue(session)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    @session_id_match_or_admin
    def put(self, session_id):
        try:
            session = get_object(SESSION, session_id)
        except ObjectNotFoundError:
            return not_found(SESSION, session_id)

        new_data = load_request_into_object(SESSION)
        models.Session.query.filter_by(uuid=session_id).update(new_data)
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
    def get(self, user_id, _range=None, order="ascending"):
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
        if request.get_json():
            try:
                session = load_request_into_object(SESSION)
                if session.user_id != utilities.current_user_id():
                    if 'admin' not in utilities.current_rolenames():
                        return forbidden_error("only admins can create sessions for other users")
                    if not is_user_present(session.user_id):
                        return forbidden_error("cannot create a session for a non-existent user")
            except SchemaValidationError as e:
                return schema_validation_error(str(e))

        else:
            session = models.Session()
            session.user_id = get_user_object_by_int_id(utilities.current_user_id()).uuid

        db.session.add(session)
        db.session.commit()

        user_obj = get_user_object(session.user_id)

        return {'uuid': str(session.uuid), 'user_uuid': str(user_obj.uuid), 'message': 'Session {} created'.format(str(session.uuid))}, 201

