from flask import jsonify
from app import schemas, db, models, utilities
from flask_restful import reqparse, Resource
import flask_praetorian
from flask_praetorian import utilities
from app import sessionApi as api
from app.exceptions import InvalidRangeError, ObjectNotFoundError

parser = reqparse.RequestParser()
parser.add_argument('user')
sessionSchema = schemas.SessionSchema()
from app.views.functions.viewfunctions import get_range
from app.views.functions.userfunctions import get_user_object, is_user_present
from app.views.functions.sessionfunctions import session_id_match_or_admin
from app.views.functions.errors import forbidden_error, not_found, unauthorised_error, internal_error
from app.utilities import get_object
from app.utilities import add_item_to_delete_queue

SESSION = models.Objects.SESSION

session_schema = schemas.SessionSchema()

class Session(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        try:
            session = get_object(SESSION, _id)
        except ObjectNotFoundError:
            return not_found(SESSION, _id)

        return jsonify(session_schema.dump(session).data)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    @session_id_match_or_admin
    def delete(self, _id):
        try:
            session = get_object(SESSION, _id)
        except ObjectNotFoundError:
            return not_found(SESSION, _id)

        return add_item_to_delete_queue(session)

api.add_resource(Session,
                 '/<_id>')

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

        result = []

        for i in items:
            result.append({"id": str(i.id), "username": user.username, "timestamp": str(i.timestamp)})


        return jsonify({"sessions": result})

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        session = models.Session()

        parser = reqparse.RequestParser()
        parser.add_argument('user')
        args = parser.parse_args()

        if args['user']:
            if 'admin' not in utilities.current_rolenames():
                return unauthorised_error("only admins can create sessions for other users")
            if not is_user_present(args['user']):
                return forbidden_error("cannot create a session for a non-existent user")
            session.user_id = args['user']
        else:
            session.user_id = utilities.current_user_id()

        db.session.add(session)
        db.session.commit()

        return {'uuid': str(session.uuid), 'user_uuid': str(session.user_id), 'message': 'Session {} created'.format(str(session.uuid))}, 201

api.add_resource(Sessions,
                 's',
                 's/<user_id>',
                 's/<user_id>/<_range>',
                 's/<user_id>/<_range>/<order>')
