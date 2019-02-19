class ObjectNotFoundError(Exception):
    """Raise when it was not possible to find an object in the database"""


class SchemaValidationError(Exception):
    """Raise when there is an error validating input with a schema"""
