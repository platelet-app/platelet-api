from app import search_ns as ns
from app import models
from flask import request, jsonify
import flask_praetorian
from flask_restplus import Resource
from app.search import query_index
from app import schemas

search_schema = schemas.SearchSchema()
users_schema = schemas.UserSchema(many=True, exclude=("address",
                                                      "dob",
                                                      "email",
                                                      "notes",
                                                      "password",
                                                      "name",
                                                      "roles",
                                                      "patch",
                                                      "tasks"))

# TODO: full search doesn't work yet
@ns.route('',
          endpoint='search_query')
class Query(Resource):
    @flask_praetorian.auth_required
    def get(self):
        request_json = request.get_json()
        query_data = search_schema.load(request_json).data
        query, total = query_index(None, query_data['query'], 1, 100)
        print(query.all())
        result = users_schema.dump(query.all()).data
        return jsonify({"total": total, "results": result})

@ns.route('/users',
          endpoint='search_users_query')
class Query(Resource):
    @flask_praetorian.auth_required
    def get(self):
        request_json = request.get_json()
        query_data = search_schema.load(request_json).data
        query, total = models.User.search(query_data['query'], int(query_data['page']) if 'page' in query_data else 1, 100)
        print(query.all())
        result = users_schema.dump(query.all()).data
        return jsonify({"total": total, "results": result})

