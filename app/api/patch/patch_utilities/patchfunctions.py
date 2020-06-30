from app import models


def get_all_patches():
    patches = models.Patch.query.all()
    if not patches:
        return {}
    return patches
