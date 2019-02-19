from flask import jsonify
from app import schemas, db, models
from flask_restful import reqparse, Resource
import flask_praetorian
from app import sessionApi as api
from app.views.functions.viewfunctions import *
from app.views.functions.userfunctions import get_user_object, is_user_present
from app.views.functions.sessionfunctions import *
from app.views.functions.errors import *

session_schema = schemas.SessionSchema()
default_delete_time = 10


class Session(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        try:
            session = get_session_object(_id)
        except ObjectNotFoundError:
            return not_found("session", _id)

        return jsonify(session_schema.dump(session).data)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    @session_id_match_or_admin
    def delete(self, _id):
        try:
            session = get_session_object(_id)
        except ObjectNotFoundError:
            return not_found("session", _id)

        if session.flaggedForDeletion:
            return forbidden_error("this session is already flagged for deletion")

        session.flaggedForDeletion = True

        delete = models.DeleteFlags(objectId=_id, objectType=models.Objects.SESSION, timeToDelete=default_delete_time)

        db.session.add(session)
        db.session.add(delete)
        db.session.commit()

        return {'id': _id, 'message': "Session {} queued for deletion".format(session.id)}, 202

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
        except ValueError as e:
            return forbidden_error(str(e))

        result = {}

        for i in items:
            result[str(i.id)] = {user.username: str(i.timestamp)}

        return result, 200

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

        return {'id': session.id, 'user_id': session.user_id, 'message': 'Session {} created'.format(session.id)}, 201

api.add_resource(Sessions,
                 's',
                 's/<user_id>',
                 's/<user_id>/<_range>',
                 's/<user_id>/<_range>/<order>')
