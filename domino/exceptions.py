class DominoException(Exception):
    """Base class for Domino Exceptions"""
    pass


class RunNotFoundException(DominoException):
    """Run Not Found Exception"""
    pass


class RunFailedException(DominoException):
    """Run Failed Exception"""
    pass


class EnvironmentNotFoundException(DominoException):
    """Environment not found Exception"""
    pass


class HardwareTierNotFoundException(DominoException):
    """Hardware tier not found Exception"""
    pass


class CommitNotFoundException(DominoException):
    """Commit not found Exception"""
    pass


class OnDemandSparkClusterNotSupportedException(DominoException):
    """On Demand Spark Cluster not supported"""
    pass


class UserNotFoundException(DominoException):
    """User not found Exception"""
    pass
