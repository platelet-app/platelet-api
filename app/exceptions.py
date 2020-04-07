class ObjectNotFoundError(Exception):
    """Raise when it was not possible to find an object in the database"""

class InvalidRangeError(Exception):
    """Raise when an invalid range was requested"""

class SchemaValidationError(Exception):
    """Raise when there is an error validating input with a schema"""

class AlreadyFlaggedForDeletionError(Exception):
    """Raise when an object that was requested to be deleted already is flagged for deletion"""
