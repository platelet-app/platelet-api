from app import schemas, models
from flask_restx import Resource, reqparse
import flask_praetorian
from app import log_ns as ns
from app.api.functions.errors import not_found
from app.exceptions import ObjectNotFoundError
from app.api.functions.utilities import get_query, get_page

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
class Logs(Resource):
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

        return logs_schema.dump(items)
