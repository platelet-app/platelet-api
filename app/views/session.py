from flask import request
from flask import jsonify
from sqlalchemy import exc as sqlexc
from app import models
from app import ma
from app import schemas
from flask_restful import reqparse, abort, Api, Resource
import flask_praetorian
from app import db
from app import sessionApi as api
from app import guard
import sys
import traceback

parser = reqparse.RequestParser()
parser.add_argument('user')
sessionSchema = schemas.SessionSchema()
from .viewfunctions import *
from datetime import datetime

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

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        pass

class Sessions(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        args = parser.parse_args()
        session = models.Session()

        db.session.add(saveValues(session, args))
        db.session.commit()

        return {'id': session.id, 'message': 'Session {} created'.format(session.id)}, 201


api.add_resource(Sessions,
                 's')
api.add_resource(Session,
                '/<_id>')

def getSessionObject(_id):

    return models.Session.query.filter_by(id=_id).first()

def saveValues(session, args):
    if args['user']: session.user_id = args['user']

    return session
