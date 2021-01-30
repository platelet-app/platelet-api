class ObjectNotFoundError(Exception):
    """Raise when it was not possible to find an object in the database"""


class ModelNotFoundError(Exception):
    """Raise when the model does not exist in the database"""


class InvalidRangeError(Exception):
    """Raise when an invalid range was requested"""


class SchemaValidationError(Exception):
    """Raise when there is an error validating input with a schema"""


class AlreadyFlaggedForDeletionError(Exception):
    """Raise when an object that was requested to be deleted already is flagged for deletion"""


class InvalidFileUploadError(Exception):
    """Raise when an invalid file is uploaded for a specific purpose"""


class ProtectedFieldError(Exception):
    """Raise when an attempt to write to a protected field is made"""