from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import deliverable_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error
from app.utilities import get_object, add_item_to_delete_queue
from app.exceptions import ObjectNotFoundError
from app import db

DELIVERABLE = models.Objects.DELIVERABLE

deliverableSchema = schemas.DeliverableSchema()


@ns.route('/<deliverable_id>')
class Deliverable(Resource):
    @flask_praetorian.auth_required
    def get(self, deliverable_id):
        if not deliverable_id:
            return not_found(DELIVERABLE)

        note = get_object(DELIVERABLE, deliverable_id)

        if note:
            return jsonify(deliverableSchema.dump(note).data)
        else:
            return not_found(deliverable_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, deliverable_id):
        try:
            note = get_object(DELIVERABLE, deliverable_id)
        except ObjectNotFoundError:
            return not_found(DELIVERABLE, deliverable_id)

        return add_item_to_delete_queue(note)

    @flask_praetorian.roles_required('admin', 'coordinator')
    def put(self, deliverable_id):
        try:
            deliverable = get_object(DELIVERABLE, deliverable_id)
        except ObjectNotFoundError:
            return not_found(DELIVERABLE, deliverable_id)

        new_data = load_request_into_object(DELIVERABLE)
        models.Session.query.filter_by(uuid=deliverable_id).update(new_data)
        db.session.commit()
        return {'uuid': str(deliverable.uuid), 'message': 'Deliverable {} updated.'.format(deliverable.uuid)}, 200


@ns.route('s')
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

