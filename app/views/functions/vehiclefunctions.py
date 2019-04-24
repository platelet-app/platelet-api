from app import models

def get_vehicle_object(_id):
    return models.Vehicle.query.filter_by(id=_id).first()

def get_all_vehicles():
    vehicles = models.Vehicle.query.all()
    if not vehicles:
        return {}
    return vehicles
