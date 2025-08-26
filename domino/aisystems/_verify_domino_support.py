import logging
import mlflow
import os
import semver
from urllib.parse import urljoin

from domino.exceptions import UnsupportedOperationException
from ..authentication import get_auth_by_type
from ._constants import MIN_MLFLOW_VERSION, MIN_DOMINO_VERSION
from ..http_request_manager import _HttpRequestManager

# not thread safe. I am not sure if this will be a problem for users, so am not implementing locking
global supported
supported = None

def _get_version_endpoint() -> str:
    return urljoin(os.environ['DOMINO_API_HOST'], "version")

def _get_domino_version() -> str:
    req_manager = _HttpRequestManager(
        get_auth_by_type()
    )
    version_metadata = req_manager.get(_get_version_endpoint()).json()
    return version_metadata["version"]

def _get_mlflow_version() -> str:
        """
        This makes testing easier
        """
        return mlflow.__version__

def _verify_domino_support_impl():
    domino_supported = True
    try:
        # we do our best to get the Domino version. If this code runs in a Domino execution,
        # auth environment variables will be available. If they run this against a local mlflow server/not
        # Domino, it is ok if this check fails
        version = _get_domino_version()

        # verify Domino version is >= min domino version
        domino_supported = semver.Version.parse(version).compare(MIN_DOMINO_VERSION) > -1
    except Exception as e:
        # the user may run this outside of Domino, so we log a warning instead of failing
        logging.debug(f"Failed to get Domino version: {e}")

    if not domino_supported:
        raise UnsupportedOperationException("This version of Domino doesn’t support the aisystems package.")

    # verify mlflow sdk version
    mlflow_supported = semver.Version.parse(_get_mlflow_version()).compare(MIN_MLFLOW_VERSION) > -1

    if not mlflow_supported:
        raise UnsupportedOperationException(f"This code requires you to install mlflow>={MIN_MLFLOW_VERSION}")

def verify_domino_support():
    global supported
    if supported is None:
        _verify_domino_support_impl()
        supported = True
