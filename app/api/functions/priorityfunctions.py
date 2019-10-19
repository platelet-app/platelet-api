from app import models

def get_all_priorities():
    priorities = models.Priority.query.all()
    if not priorities:
        return {}
    return priorities
