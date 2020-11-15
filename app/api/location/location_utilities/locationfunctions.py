from app import models
from app.exceptions import ObjectNotFoundError


def get_location_object(_id, with_deleted=False):
    if with_deleted:
        location = models.Location.query.with_deleted().filter_by(uuid=_id).first()
    else:
        location = models.Location.query.filter_by(uuid=_id).first()
    if not location:
        raise ObjectNotFoundError

    return location


def get_all_locations(filter_deleted=False):
    if filter_deleted:
        return models.Location.query.all()
    else:
        return models.Location.query.with_deleted().all()
