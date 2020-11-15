from app import models
from app.exceptions import ObjectNotFoundError


def get_deliverable_object(_id, with_deleted=False):
    if with_deleted:
        deliverable = models.Deliverable.query.with_deleted().filter_by(uuid=_id).first()
    else:
        deliverable = models.Deliverable.query.filter_by(uuid=_id).first()
    if not deliverable:
        raise ObjectNotFoundError()
    return deliverable


def get_deliverable_type(_id):
    return models.DeliverableType.query.filter_by(id=_id).first()


def get_all_deliverable_types(filter_deleted=False):
    if filter_deleted:
        return models.DeliverableType.query.all()
    else:
        return models.DeliverableType.query.with_deleted().all()
