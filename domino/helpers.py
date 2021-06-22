import os
import socket
import urllib

from distutils.version import LooseVersion as parse_version

from .constants import *


def is_version_compatible(version: str) -> bool:
    """
    Helper function to check for version compatibility

    @:param version  Domino version to check version compatibility against
    @:return bool   Boolean representing if version is compatible or not
    """
    return parse_version(version) >= parse_version(MINIMUM_SUPPORTED_DOMINO_VERSION)

def is_cluster_type_supported(version: str, cluster_type: str) -> bool:
    curr_version = parse_version(version)

    return next(
        (True for ct,min_version in CLUSTER_TYPE_MIN_SUPPORT if ct == cluster_type and curr_version >= parse_version(min_version)),
        False
    )

def is_compute_cluster_properties_supported(version: str) -> bool:
    return parse_version(version) >= parse_version(MINIMUM_DISTRIBUTED_CLUSTER_SUPPORT_DOMINO_VERSION)


def is_on_demand_spark_cluster_supported(version: str) -> bool:
    return parse_version(version) >= parse_version(MINIMUM_ON_DEMAND_SPARK_CLUSTER_SUPPORT_DOMINO_VERSION)


def get_host_or_throw_exception(host):
    """
    Helper function to get `host` from passed variable or environment variable
    """
    if host is not None:
        _host = host
    elif DOMINO_HOST_KEY_NAME in os.environ:
        _host = os.environ[DOMINO_HOST_KEY_NAME]
    else:
        raise Exception(f"Host must be provided, either via the "
                        f"constructor value or through {DOMINO_HOST_KEY_NAME} "
                        f"environment variable.")
    return _host


def get_api_key(api_key):
    """
    Helper function to get `api_key` from passed variable or environment variable
    """
    if api_key is not None:
        _api_key = api_key
    elif DOMINO_USER_API_KEY_KEY_NAME in os.environ:
        _api_key = os.environ[DOMINO_USER_API_KEY_KEY_NAME]
    else:
        _api_key = None
    return _api_key


def get_path_to_domino_token_file(path_to_domino_token_file):
    """
    Helper function to get `path_to_domino_token_file` either
    from passed variable or environment variable
    """
    if path_to_domino_token_file is not None:
        _path_to_domino_token_file = path_to_domino_token_file
    elif DOMINO_TOKEN_FILE_KEY_NAME in os.environ:
        _path_to_domino_token_file = os.environ[DOMINO_TOKEN_FILE_KEY_NAME]
    else:
        _path_to_domino_token_file = None
    return _path_to_domino_token_file


def clean_host_url(host_url):
    """
    Helper function to clean 'host_url'. This will extract
    hostname (with scheme) from the url
    """
    url_split = urllib.parse.urlsplit(host_url)
    return f"{url_split.scheme}://{url_split.netloc}"


def domino_is_reachable(url=os.getenv(DOMINO_HOST_KEY_NAME), port="443"):
    """
    Confirm that a deployment is accessible.

    Returns Boolean value.
    """
    if url is None:
        return False

    fqdn = urllib.parse.urlsplit(url).netloc
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((fqdn, int(port)))
        is_reachable = True
    except OSError:
        print(f"{fqdn}:{port} is not reachable")
        is_reachable = False
    finally:
        s.close()

    return is_reachable
