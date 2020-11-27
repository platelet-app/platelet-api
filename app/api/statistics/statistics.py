import flask_praetorian
from flask_restx import Resource, reqparse
from sqlalchemy import union_all

from app import statistics_ns as ns, models
from app.api.functions.errors import not_found, internal_error, unprocessable_entity_error
from app.api.functions.utilities import get_object
from app.api.statistics.statistics_utilities.statistics_functions import generate_statistics_from_tasks
from app.exceptions import ObjectNotFoundError

import dateutil.parser


@ns.route(
    '/<user_uuid>',
    endpoint='user_statistics')
class TasksStatistics(Resource):
    @flask_praetorian.auth_required
    def get(self, user_uuid):
        if not user_uuid:
            return not_found(models.Objects.USER)
        try:
            requested_user = get_object(models.Objects.USER, user_uuid)
            if not requested_user:
                return not_found(models.Objects.USER, user_uuid)
            if requested_user.deleted:
                return not_found(requested_user.object_type, user_uuid)
        except ObjectNotFoundError:
            return not_found(models.Objects.USER, user_uuid)
        try:
            # TODO: add page size querystring
            parser = reqparse.RequestParser()
            parser.add_argument("role", type=str, location="args")
            parser.add_argument("start_date_time", type=str, location="args")
            parser.add_argument("end_date_time", type=str, location="args")
            args = parser.parse_args()
            role = args['role'] if args['role'] else None
            start_date_time = args['start_date_time'] if args['start_date_time'] else None
            end_date_time = args['end_date_time'] if args['end_date_time'] else None
            start_date_time = dateutil.parser.parse(start_date_time)
            end_date_time = dateutil.parser.parse(end_date_time)
            if (start_date_time > end_date_time):
                return unprocessable_entity_error("Start date time cannot be after end date time.")

            if role == "coordinator":
                query = requested_user.tasks_as_coordinator
            elif role == "rider":
                query = requested_user.tasks_as_rider
            else:
                query = union_all(requested_user.tasks_as_coordinator, requested_user.tasks_as_rider)

            if start_date_time and end_date_time:
                query_date = query.filter(models.Task.time_created.between(
                    start_date_time,
                    end_date_time)
                )
            elif start_date_time and not end_date_time:
                query_date = query.filter(models.Task.time_created >= start_date_time)
            elif not start_date_time and end_date_time:
                query_date = query.filter(models.Task.time_created <= end_date_time)
            else:
                query_date = query

            # TODO: make a schema for this
            return generate_statistics_from_tasks(query_date.all()), 200

        except Exception as e:
            return internal_error(e)
