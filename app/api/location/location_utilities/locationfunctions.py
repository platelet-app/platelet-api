from app import models


def get_location_object(_id):
    return models.Location.query.filter_by(uuid=_id).first()


def get_all_locations(filter_deleted=False):
    if filter_deleted:
        return models.Location.query.filter_by(flagged_for_deletion=False)
    else:
        return models.Location.query.all()
