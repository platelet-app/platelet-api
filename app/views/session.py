from flask import jsonify
from app import schemas
from flask_restful import reqparse, Resource
import flask_praetorian
from app import sessionApi as api

parser = reqparse.RequestParser()
parser.add_argument('user')
sessionSchema = schemas.SessionSchema()
from app.views.functions.viewfunctions import *
from app.views.functions.userfunctions import getUserObject
from app.views.functions.sessionfunctions import *


class Session(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return notFound()

        session = getSessionObject(_id)

        if (session):
            return jsonify(sessionSchema.dump(session).data)
        else:
            return notFound(_id)

    @flask_praetorian.roles_accepted('coordinator', 'admin')
    @sessionIdMatchOrAdmin
    def delete(self, _id):
        if not _id:
            return notFound("session")

        session = getSessionObject(_id)

        if not session:
            return notFound("session", _id)

        if session.flaggedForDeletion:
            return forbiddenError("this user is already flagged for deletion")

        session.flaggedForDeletion = True

        delete = models.DeleteFlags(objectId=_id, objectType=models.Objects.SESSION, timeToDelete=10)

        db.session.add(session)
        db.session.add(delete)

        db.session.commit()

        return {'id': _id, 'message': "Session {} queued for deletion".format(session.id)}, 202

class Sessions(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        args = parser.parse_args()

        if args['user']:
            print(models.User.query.filter_by(id=args['user']))
            if not models.User.query.filter_by(id=args['user']).first():
                return forbiddenError("cannot create a session for a non-existent user")

        session = models.Session()

        session.user_id = utilities.current_user_id()

        if args['user']:
            if 'admin' in utilities.current_rolenames():
                session.user_id = args['user']
            else:
                return unauthorisedError("only admins can create sessions for other users")

        db.session.add(session)
        db.session.commit()

        return {'id': session.id, 'user_id': session.user_id, 'message': 'Session {} created'.format(session.id)}, 201

    def get(self, user_id):
        user = getUserObject(user_id)
        if not user:
            return notFound('user', user_id)
        sessions = user.sessions.all()

        result = {}

        for i in sessions:
            result[str(i.id)] = {user.username: str(i.timestamp)}
            print(result)

        return result, 200


api.add_resource(Sessions,
                 's',
                 's/<user_id>')
api.add_resource(Session,
                '/<_id>')


def getSessionObject(_id):
    return models.Session.query.filter_by(id=_id).first()
