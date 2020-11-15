from app import models
from app.exceptions import ObjectNotFoundError


def get_vehicle_object(_id, with_deleted=False):
    if with_deleted:
        vehicle = models.Vehicle.query.with_deleted().filter_by(uuid=_id).first()
    else:
        vehicle = models.Vehicle.query.filter_by(uuid=_id).first()
    if not vehicle:
        raise ObjectNotFoundError()
    return vehicle


def get_all_vehicles(filter_deleted=False):
    if filter_deleted:
        return models.Vehicle.query.all()
    else:
        return models.Vehicle.query.with_deleted().all()
