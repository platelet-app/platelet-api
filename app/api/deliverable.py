from flask import jsonify
from app import schemas, models
from flask_restful import Resource
import flask_praetorian
from app import deliverableApi as api
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error
from app.utilities import get_object, add_item_to_delete_queue
from app.exceptions import ObjectNotFoundError
from app import db

DELIVERABLE = models.Objects.DELIVERABLE

deliverableSchema = schemas.DeliverableSchema()

class Deliverable(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found("deliverable")

        note = get_object(DELIVERABLE, _id)

        if note:
            return jsonify(deliverableSchema.dump(note).data)
        else:
            return not_found(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        try:
            note = get_object(DELIVERABLE, _id)
        except ObjectNotFoundError:
            return not_found("deliverable", _id)

        return add_item_to_delete_queue(note)

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

api.add_resource(Deliverable,
                 '/<_id>')
api.add_resource(Deliverables,
                 's')