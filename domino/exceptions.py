class DominoException(Exception):
    """Base class for Domino Exceptions"""

    pass


class DatasetNotFoundException(DominoException):
    """Dataset not found Exception"""

    pass


class DatasetExistsException(DominoException):
    """Dataset already exists Exception"""

    pass


class RunNotFoundException(DominoException):
    """Run not found Exception"""

    pass


class ProjectNotFoundException(DominoException):
    """Project not found Exception"""

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


class ExternalVolumeMountsNotSupportedException(DominoException):
    """External Volume Mounts not supported"""

    pass


class UserNotFoundException(DominoException):
    """User not found Exception"""

    pass


class UnsupportedFieldException(DominoException):
    """Unsupported field Exception"""

    pass


class MalformedInputException(DominoException):
    """Malformed input Exception"""

    pass


class MissingRequiredFieldException(DominoException):
    """Missing required field Exception"""

    pass


class ReloginRequiredException(DominoException):
    """Re-login required Exception"""

    pass
