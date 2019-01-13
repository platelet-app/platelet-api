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

from .viewfunctions import *
from datetime import datetime

class Session(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):


        if not _id:
            return notFound()

        user = getUserObject(_id)

        if (user):
            return jsonify(userSchema.dump(user).data)
        else:
            return notFound(_id)


    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
