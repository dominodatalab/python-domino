class DominoException(Exception):
    """Base class for Domino Exceptions"""
    pass

class RunNotFoundException(DominoException):
    """Run Not Found Exception"""
    pass

class RunFailedException(DominoException):
    """Run Failed Exception"""
    pass
