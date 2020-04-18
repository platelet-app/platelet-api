from flask import jsonify
from app import schemas, models
from flask_restplus import Resource
from flask_praetorian import utilities as prae_utils
from app import comment_ns as ns
import flask_praetorian
from app.api.functions.userfunctions import get_user_object_by_int_id
from app.api.functions.viewfunctions import load_request_into_object
from app.api.functions.errors import not_found, internal_error, forbidden_error, already_flagged_for_deletion_error
from app.utilities import get_object, add_item_to_delete_queue, get_unspecified_object
from app.exceptions import ObjectNotFoundError, AlreadyFlaggedForDeletionError
from app import db

COMMENT = models.Objects.COMMENT

comment_schema = schemas.CommentSchema()
comments_schema = schemas.CommentSchema(many=True)


@ns.route('/<_id>')
class Comment(Resource):
    @flask_praetorian.auth_required
    def get(self, _id):
        if not _id:
            return not_found("comment")

        comment = get_object(COMMENT, _id)

        if comment:
            return jsonify(comment_schema.dump(comment).data)
        else:
            return not_found(_id)

    @flask_praetorian.auth_required
    def delete(self, _id):
        try:
            comment = get_object(COMMENT, _id)
        except ObjectNotFoundError:
            return not_found("comment", _id)
        try:
            add_item_to_delete_queue(comment)
        except AlreadyFlaggedForDeletionError:
            return already_flagged_for_deletion_error(COMMENT, str(comment.uuid))

        return {'uuid': str(comment.uuid), 'message': "Comment queued for deletion"}, 202

    @flask_praetorian.auth_required
    def put(self, _id):
        try:
            comment = get_object(COMMENT, _id)
        except ObjectNotFoundError:
            return not_found(COMMENT, _id)


        load_request_into_object(COMMENT, instance=comment)
        db.session.commit()
        return {'uuid': str(comment.uuid), 'message': 'Comment {} updated.'.format(comment.uuid)}, 200


@ns.route('s',
          's/<parent_id>')
class Comments(Resource):
    @flask_praetorian.auth_required
    def post(self):
        calling_user = get_user_object_by_int_id(prae_utils.current_user_id()).uuid
        try:
            comment = load_request_into_object(COMMENT)
        except Exception as e:
            return internal_error(e)

        parent = get_unspecified_object(comment.parent_uuid)
        comment.parent_type = parent.object_type
        comment.parent_uuid = parent.uuid
        if not comment.author:
            comment.author_uuid = calling_user

        db.session.add(comment)
        db.session.commit()

        return {'uuid': str(comment.uuid), 'message': 'Comment {} created'.format(comment.uuid)}, 201

    @flask_praetorian.auth_required
    def get(self, parent_id):
        calling_user = get_user_object_by_int_id(prae_utils.current_user_id()).uuid
        try:
            parent = get_unspecified_object(parent_id)
        except ObjectNotFoundError:
            return not_found(COMMENT, parent_id)
        if hasattr(parent, "comments"):
            result = filter(lambda comment: comment.publicly_visible or comment.author.uuid == calling_user, parent.comments)
            return jsonify(comments_schema.dump(result).data)
        else:
            return forbidden_error("{} does not support comments.".format(parent), parent_id)
