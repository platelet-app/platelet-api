from flask import jsonify, request
from app import schemas, db, models, utilities
from flask_restplus import reqparse, Resource
import flask_praetorian
from flask_praetorian import utilities
from app import session_ns as ns
from app.exceptions import InvalidRangeError, ObjectNotFoundError, SchemaValidationError
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.viewfunctions import get_range
from app.api.functions.userfunctions import get_user_object, is_user_present
from app.api.functions.sessionfunctions import session_id_match_or_admin
from app.api.functions.errors import forbidden_error, not_found, unauthorised_error, internal_error, schema_validation_error
from app.utilities import get_object
from app.utilities import add_item_to_delete_queue
import uuid

SESSION = models.Objects.SESSION

session_schema = schemas.SessionSchema()
sessions_schema = schemas.SessionSchema(many=True)


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
            return not_found("user", user_id)

        try:
            items = get_range(user.sessions.all(), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return sessions_schema.jsonify(items)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        user = None

        if request.get_json():
            try:
                session = load_request_into_object(SESSION)
            except SchemaValidationError as e:
                return schema_validation_error(str(e))

            user = session.user_id

        else:
            session = models.Session()

        if user:
            if 'admin' not in utilities.current_rolenames():
                return unauthorised_error("only admins can create sessions for other users")
            if not is_user_present(user):
                return forbidden_error("cannot create a session for a non-existent user")
            session.user_id = user
        else:
            session.user_id = uuid.UUID(utilities.current_user_id())

        db.session.add(session)
        db.session.commit()

        return {'uuid': str(session.uuid), 'user_uuid': str(session.user_id), 'message': 'Session {} created'.format(str(session.uuid))}, 201

