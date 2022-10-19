from pprint import pformat, pprint

import pytest

from domino.helpers import domino_is_reachable


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_list_environments(default_domino_client):
    """
    Confirm that python-domino client can list environments (v1 API).
    """
    env_list = default_domino_client.environments_list()
    assert (
        env_list["objectType"] == "list"
    ), f"environments_list returned unexpected result:\n{pformat(env_list)}"
    assert any(
        "Domino Standard Environment" in env["name"] for env in env_list["data"]
    ), "Could not find Domino Standard Environment in environment list"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_list_usable_environments(default_domino_client):
    """
    Confirm that python-domino client can list environments (v4 API).
    """
    env_list = default_domino_client._useable_environments_list()
    assert isinstance(
        env_list, list
    ), f"_useable_environments_list returned unexpected result:\n{pformat(env_list)}"
    assert any(
        "Domino Standard Environment" in env["name"] for env in env_list
    ), "Could not find Domino Standard Environment in environment list"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_in_environments(default_domino_client):
    """
    Confirm that python-domino client can list environments (v1 API).
    """
    env_list = default_domino_client.environments_list()
    assert (
        env_list["objectType"] == "list"
    ), f"environments_list returned unexpected result:\n{pformat(env_list)}"

    for env in env_list["data"]:
        if "Spark Cluster Environment" in env["name"]:
            pprint(env)

    assert any(
        "Spark Cluster Environment" in env["name"] for env in env_list["data"]
    ), "Could not find Domino Standard Environment in environment list"

