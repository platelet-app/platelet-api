from app import models

def get_all_priorities(filter_deleted=False):
    if filter_deleted:
        return models.Priority.query.all()
    else:
        return models.Priority.query.with_deleted().all()
