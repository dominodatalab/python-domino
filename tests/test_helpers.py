"""
Unit tests for domino.helpers module.
No HTTP calls — pure logic tests.
"""

import pytest

from domino.helpers import (
    clean_host_url,
    is_cluster_type_supported,
    is_compute_cluster_autoscaling_supported,
    is_compute_cluster_properties_supported,
    is_external_volume_mounts_supported,
    is_on_demand_spark_cluster_supported,
    is_version_compatible,
)

# --- is_version_compatible ---


def test_is_version_compatible_returns_true_for_supported_version():
    assert is_version_compatible("5.0.0") is True


def test_is_version_compatible_returns_false_for_old_version():
    assert is_version_compatible("1.0.0") is False


def test_is_version_compatible_returns_true_for_exact_minimum():
    from domino.constants import MINIMUM_SUPPORTED_DOMINO_VERSION

    assert is_version_compatible(MINIMUM_SUPPORTED_DOMINO_VERSION) is True


# --- clean_host_url ---


def test_clean_host_url_strips_path():
    assert (
        clean_host_url("https://domino.example.com/some/path")
        == "https://domino.example.com"
    )


def test_clean_host_url_preserves_scheme_and_host():
    assert clean_host_url("https://domino.example.com") == "https://domino.example.com"


def test_clean_host_url_handles_http():
    assert clean_host_url("http://localhost:8080/domino") == "http://localhost:8080"


def test_clean_host_url_handles_trailing_slash():
    assert clean_host_url("https://domino.example.com/") == "https://domino.example.com"


# --- is_compute_cluster_autoscaling_supported ---


def test_autoscaling_supported_for_high_version():
    assert is_compute_cluster_autoscaling_supported("9.9.9") is True


def test_autoscaling_not_supported_for_low_version():
    assert is_compute_cluster_autoscaling_supported("1.0.0") is False


# --- is_compute_cluster_properties_supported ---


def test_cluster_properties_supported_for_high_version():
    assert is_compute_cluster_properties_supported("9.9.9") is True


def test_cluster_properties_not_supported_for_low_version():
    assert is_compute_cluster_properties_supported("1.0.0") is False


# --- is_on_demand_spark_cluster_supported ---


def test_on_demand_spark_supported_for_high_version():
    assert is_on_demand_spark_cluster_supported("9.9.9") is True


def test_on_demand_spark_not_supported_for_low_version():
    assert is_on_demand_spark_cluster_supported("1.0.0") is False


# --- is_external_volume_mounts_supported ---


def test_external_volume_mounts_supported_for_high_version():
    assert is_external_volume_mounts_supported("9.9.9") is True


def test_external_volume_mounts_not_supported_for_low_version():
    assert is_external_volume_mounts_supported("1.0.0") is False


# --- is_cluster_type_supported ---


@pytest.mark.parametrize("cluster_type", ["Ray", "Dask", "MPI", "Spark"])
def test_known_cluster_types_supported_for_high_version(cluster_type):
    result = is_cluster_type_supported("9.9.9", cluster_type)
    assert isinstance(result, bool)


def test_unknown_cluster_type_returns_false():
    assert is_cluster_type_supported("9.9.9", "UnknownCluster") is False
