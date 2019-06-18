from app import models

def get_location_object(_id):
    return models.Location.query.filter_by(uuid=_id).first()

def get_all_locations():
    locations = models.Location.query.all()
    if not locations:
        return {}
    return locations
