from app import models


def get_all_patches(filter_deleted=False):
    if filter_deleted:
        return models.Patch.query.all()
    else:
        return models.Patch.query.with_deleted().all()
