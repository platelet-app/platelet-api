from app import models
from app.exceptions import ObjectNotFoundError

def get_vehicle_object(_id):
    vehicle = models.Vehicle.query.filter_by(uuid=_id).first()
    if not vehicle:
        raise ObjectNotFoundError()
    return vehicle

def get_all_vehicles():
    vehicles = models.Vehicle.query.all()
    if not vehicles:
        return {}
    return vehicles
