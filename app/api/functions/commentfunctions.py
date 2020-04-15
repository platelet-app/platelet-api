from app import models
from app.exceptions import ObjectNotFoundError

def get_comment_object(_id):
    result = models.Comment.query.filter_by(uuid=_id).first()
    if not result:
        raise ObjectNotFoundError("comment id: {} not found".format(_id))
    return result
