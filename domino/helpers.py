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

def is_comute_cluster_autoscaling_supported(version: str) -> bool:
    return parse_version(version) >= parse_version(COMPUTE_CLUSTER_AUTOSCALING_MIN_SUPPORT_DOMINO_VERSION)

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

def is_external_volume_mounts_supported(version: str) -> bool:
    return parse_version(version) >= parse_version(MINIMUM_EXTERNAL_VOLUME_MOUNTS_SUPPORT_DOMINO_VERSION)

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
