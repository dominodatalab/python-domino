from distutils.version import LooseVersion as parse_version
from .constants import MINIMUM_SUPPORTED_DOMINO_VERSION


def is_version_compatible(version: str) -> bool:
    """
    Helper function to check for version compatibility

    @:param version  Domino version to check version compatibility against

    @:return bool   Boolean representing if version is compatible or not
    """
    return parse_version(version) >= parse_version(MINIMUM_SUPPORTED_DOMINO_VERSION)
