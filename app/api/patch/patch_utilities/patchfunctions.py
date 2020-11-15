from app import models


def get_all_patches(filter_deleted=False):
    if filter_deleted:
        return models.Patch.query.filter_by(deleted=False)
    else:
        return models.Patch.query.all()
