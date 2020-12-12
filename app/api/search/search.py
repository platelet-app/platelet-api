from app import search_ns as ns
from app import models
from flask import request, jsonify
import flask_praetorian
from flask_restx import Resource
from app.search import query_index
from app import schemas

search_schema = schemas.SearchSchema()
users_schema = schemas.UserSchema(many=True, exclude=("address",
                                                      "dob",
                                                      "email",
                                                      "password",
                                                      "name",
                                                      "roles",
                                                      "patch",))


tasks_schema = schemas.TaskSchema(many=True)

locations_schema = schemas.LocationSchema(many=True)

vehicles_schema = schemas.VehicleSchema(many=True)

# TODO: full search doesn't work yet
@ns.route('',
          endpoint='search_query')
class Query(Resource):
    @flask_praetorian.auth_required
    def get(self):
        request_json = request.get_json()
        query_data = search_schema.load(request_json).data
        query, total = query_index(None, query_data['query'], 1, 100)
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
        result = users_schema.dump(query.all()).data
        return jsonify({"total": total, "results": result})


@ns.route('/tasks',
          endpoint='search_tasks_query')
class Query(Resource):
    @flask_praetorian.auth_required
    def get(self):
        request_json = request.get_json()
        query, total = models.Task.search(request_json['query'], int(request_json['page']) if 'page' in request_json else 1, 100)
        result = tasks_schema.dump(query.all())
        return jsonify({"total": total, "results": result})

@ns.route('/locations',
          endpoint='search_locations_query')
class Query(Resource):
    @flask_praetorian.auth_required
    def get(self):
        request_json = request.get_json()
        query_data = search_schema.load(request_json).data
        query, total = models.Location.search(query_data['query'], int(query_data['page']) if 'page' in query_data else 1, 100)
        result = locations_schema.dump(query.all()).data
        return jsonify({"total": total, "results": result})

@ns.route('/vehicles',
          endpoint='search_vehicles_query')
class Query(Resource):
    @flask_praetorian.auth_required
    def get(self):
        request_json = request.get_json()
        query_data = search_schema.load(request_json).data
        query, total = models.Vehicle.search(query_data['query'], int(query_data['page']) if 'page' in query_data else 1, 100)
        result = vehicles_schema.dump(query.all()).data
        return jsonify({"total": total, "results": result})

