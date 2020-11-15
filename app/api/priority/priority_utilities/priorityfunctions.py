from app import models

def get_all_priorities(filter_deleted=False):
    if filter_deleted:
        return models.Priority.query.filter_by(deleted=False)
    else:
        return models.Priority.query.all()
