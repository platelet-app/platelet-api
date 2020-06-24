from flask import jsonify
from app import schemas, models
from flask_restx import Resource
import flask_praetorian
from app import deliverable_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error, already_flagged_for_deletion_error
from app.utilities import get_object, add_item_to_delete_queue, get_all_objects, get_range
from app.exceptions import ObjectNotFoundError, InvalidRangeError, AlreadyFlaggedForDeletionError
from app import db

DELIVERABLE = models.Objects.DELIVERABLE
DELIVERABLE_TYPE = models.Objects.DELIVERABLE_TYPE
TASK = models.Objects.TASK

deliverable_schema = schemas.DeliverableSchema()
deliverables_schema = schemas.DeliverableSchema(many=True)
deliverable_types_schema = schemas.DeliverableTypeSchema(many=True)


@ns.route('s/available')
class DeliverableType(Resource):
    @flask_praetorian.auth_required
    def get(self):
        deliverable_types = get_all_objects(DELIVERABLE_TYPE)
        return jsonify(deliverable_types_schema.dump(deliverable_types))



@ns.route('/<deliverable_id>')
class Deliverable(Resource):
    @flask_praetorian.auth_required
    def get(self, deliverable_id):
        if not deliverable_id:
            return not_found(DELIVERABLE)

        deliverable = get_object(DELIVERABLE, deliverable_id)

        if deliverable:
            return jsonify(deliverable_schema.dump(deliverable))
        else:
            return not_found(deliverable_id)

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    def delete(self, deliverable_id):
        try:
            deliverable = get_object(DELIVERABLE, deliverable_id)
        except ObjectNotFoundError:
            return not_found(DELIVERABLE, deliverable_id)
        try:
            add_item_to_delete_queue(deliverable)
        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(DELIVERABLE, str(deliverable.uuid))

        return {'uuid': str(deliverable.uuid), 'message': "Deliverable queued for deletion"}, 202

    @flask_praetorian.roles_accepted('admin', 'coordinator')
    def put(self, deliverable_id):
        try:
            deliverable = get_object(DELIVERABLE, deliverable_id)
        except ObjectNotFoundError:
            return not_found(DELIVERABLE, deliverable_id)

        load_request_into_object(DELIVERABLE, instance=deliverable)
        db.session.commit()
        return {'uuid': str(deliverable.uuid), 'message': 'Deliverable {} updated.'.format(deliverable.uuid)}, 200


@ns.route('s',
          's/<task_id>')
class Deliverables(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        try:
            deliverable = load_request_into_object(DELIVERABLE)
        except Exception as e:
            return internal_error(e)

        db.session.add(deliverable)
        db.session.commit()

        return {'uuid': str(deliverable.uuid), 'message': 'Deliverable {} created'.format(deliverable.uuid)}, 201

    @flask_praetorian.auth_required
    def get(self, task_id, _range=None, order="ascending"):
        try:
            task = get_object(TASK, task_id)
        except ObjectNotFoundError:
            return not_found(TASK, task_id)

        try:
            items = get_range(task.deliverables.all(), _range, order)
        except InvalidRangeError as e:
            return forbidden_error(e)
        except Exception as e:
            return internal_error(e)

        return deliverables_schema.jsonify(items)
