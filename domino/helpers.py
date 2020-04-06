from distutils.version import LooseVersion as parse_version
from .constants import MINIMUM_SUPPORTED_DOMINO_VERSION
from version import PYTHON_DOMINO_VERSION


def is_version_compatible(version: str) -> None:
    """
    Helper function to check for version compatibility

    @:param version  Domino version to check version compatibility against

    @:exception throws exception if domino version isn't compatible with
                current python-domino version
    """
    current_version = parse_version(version)
    minimum_supported_version = parse_version(MINIMUM_SUPPORTED_DOMINO_VERSION)
    is_compatible = current_version > minimum_supported_version
    if not is_compatible:
        raise Exception(f"Domino version: {version} is not compatible \
        with python-domino version: {PYTHON_DOMINO_VERSION}")
