from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
import flask_praetorian
from app import note_ns as ns
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error
from app.utilities import get_object, add_item_to_delete_queue
from app.exceptions import ObjectNotFoundError
from app import db

NOTE = models.Objects.NOTE

noteSchema = schemas.NoteSchema()


@ns.route('/<_id>')
class Note(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found("note")

        note = get_object(NOTE, _id)

        if note:
            return jsonify(noteSchema.dump(note).data)
        else:
            return not_found(_id)

    @flask_praetorian.roles_required('admin')
    def delete(self, _id):
        try:
            note = get_object(NOTE, _id)
        except ObjectNotFoundError:
            return not_found("note", _id)

        return add_item_to_delete_queue(note)


@ns.route('s')
class Notes(Resource):
    @flask_praetorian.roles_accepted('coordinator', 'admin')
    def post(self):
        try:
            note = load_request_into_object(NOTE)
        except Exception as e:
            return internal_error(e)


        db.session.add(note)
        db.session.commit()

        return {'uuid': str(note.uuid), 'message': 'Note {} created'.format(note.uuid)}, 201

