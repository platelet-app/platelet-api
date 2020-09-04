from app import models


def get_deliverable_object(_id):
    return models.Deliverable.query.filter_by(uuid=_id).first()


def get_deliverable_type(_id):
    return models.DeliverableType.query.filter_by(id=_id).first()


def get_all_deliverable_types(filter_deleted=False):
    if filter_deleted:
        return models.DeliverableType.query.filter_by(flagged_for_deletion=False)
    else:
        return models.DeliverableType.query.all()
