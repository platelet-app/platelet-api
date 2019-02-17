class ObjectNotFoundError(Exception):
    """Raise when it was not possible to find an object in the database"""

class InvalidRangeError(Exception):
    """Raise when an invalid range was requested"""
