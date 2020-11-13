from sqlalchemy import union_all
from sqlalchemy.orm import joinedload

from app import schemas, models
from flask_restx import Resource, reqparse
import flask_praetorian
from app import log_ns as ns
from app.api.functions.errors import not_found
from app.exceptions import ObjectNotFoundError
from app.api.functions.utilities import get_query, get_page, get_object

logs_schema = schemas.LogEntrySchema(many=True)

LOG_ENTRY = models.Objects.LOG_ENTRY


@ns.route('s', endpoint="all_logs")
class Logs(Resource):
    @flask_praetorian.roles_accepted("admin")
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", type=int, location="args")
        parser.add_argument("order", type=str, location="args")
        args = parser.parse_args()
        page = args['page'] if args['page'] else 1
        order = args['order'] if args['order'] else "newest"
        query = get_query(LOG_ENTRY)
        try:
            items = get_page(query, page, order=order, model=models.LogEntry)
        except ObjectNotFoundError:
            return not_found(LOG_ENTRY)
        return logs_schema.dump(items)


@ns.route('s/<object_uuid>', endpoint="object_logs")
class ObjectLogs(Resource):
    @flask_praetorian.auth_required
    def get(self, object_uuid):
        parser = reqparse.RequestParser()
        parser.add_argument("page", type=int, location="args")
        parser.add_argument("order", type=str, location="args")
        args = parser.parse_args()
        page = args['page'] if args['page'] else 0
        order = args['order'] if args['order'] else "newest"
        query = get_query(LOG_ENTRY)
        filtered = query.filter_by(parent_uuid=object_uuid)
        if page > 0:
            try:
                items = get_page(filtered, page, order=order, model=models.LogEntry)
            except ObjectNotFoundError:
                return not_found(LOG_ENTRY)
        else:
            items = filtered.all()
            if order != "newest":
                items.reverse()

        return logs_schema.dump(items)


@ns.route('s/<user_uuid>/user_tasks_log_record', endpoint="user_tasks_log_record")
class MyLogs(Resource):
    @flask_praetorian.auth_required
    def get(self, user_uuid):
        parser = reqparse.RequestParser()
        parser.add_argument("page", type=int, location="args")
        parser.add_argument("order", type=str, location="args")
        parser.add_argument("role", type=str, location="args")
        parser.add_argument("return", type=str, location="args")
        args = parser.parse_args()
        page = args['page'] if args['page'] else 1
        order = args['order'] if args['order'] else "newest"
        role = args['role'] if args['role'] else None
        returns = args['return'] if args['return'] else "everything"
        # everything, mine_only, others_only

        user = get_object(models.Objects.USER, user_uuid)

        if role == "coordinator":
            query = user.tasks_as_coordinator
        elif role == "rider":
            query = user.tasks_as_rider
        else:
            query = user.tasks_as_coordinator



        #TODO: figure out how to do this with sqlalchemy so pages work and it isn't so inefficent
        logs = []
        if returns == "everything":
            for i in query.all():
                for l in i.logged_actions:
                    logs.append(l)
        elif returns == "mine_only":
            for i in query.all():
                for l in i.logged_actions:
                    if str(l.calling_user_uuid) == user_uuid:
                        logs.append(l)
        elif returns == "others_only":
            for i in query.all():
                for l in i.logged_actions:
                    if str(l.calling_user_uuid) != user_uuid:
                        logs.append(l)

        return logs_schema.dump(logs)
