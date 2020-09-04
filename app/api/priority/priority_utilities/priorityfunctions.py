from app import models

def get_all_priorities(filter_deleted=False):
    if filter_deleted:
        return models.Priority.query.filter_by(flagged_for_deletion=False)
    else:
        return models.Priority.query.all()
