import pytest
from domino import Domino


def test_versioning(requests_mock, dummy_hostname):
    """validates domino version checking is correct"""

    # Mock a typical response from the jobs status API endpoint (GET)
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "5.10.0"})

    dom = Domino(host=dummy_hostname, project="rand_user/rand_project", api_key="rand_api_key")

    dep_version = dom.deployment_version().get("version")
    assert dep_version == "5.10.0"
    assert dom.requires_at_least("5.3.0")
    with pytest.raises(Exception):
        dom.requires_at_least("5.11.0")

