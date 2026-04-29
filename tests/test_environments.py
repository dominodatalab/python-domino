from pprint import pformat, pprint

import pytest

from domino import Domino
from domino.helpers import domino_is_reachable

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_ENV_ID = "aabbccddeeff001122334458"

MOCK_ENVIRONMENT = {
    "id": MOCK_ENV_ID,
    "name": "my-env",
    "visibility": "Private",
    "latestRevisionDetails": {
        "dockerImage": "ubuntu:20.04",
    },
}


@pytest.fixture
def base_mocks(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID},
    )
    yield


# ---------------------------------------------------------------------------
# Unit tests (no live Domino deployment required)
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_environments_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v1/environments", json=[MOCK_ENVIRONMENT])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.environments_list()
    assert isinstance(result, list)
    assert result[0]["id"] == MOCK_ENV_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_default_environment_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/environments/defaultEnvironment", json=MOCK_ENVIRONMENT
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_default_environment()
    assert result["id"] == MOCK_ENV_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_environment_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/api/environments/v1/environments/{MOCK_ENV_ID}",
        json=MOCK_ENVIRONMENT,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_environment(MOCK_ENV_ID)
    assert result["name"] == "my-env"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_archive_environment_sends_delete(requests_mock, dummy_hostname):
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/api/environments/v1/environments/{MOCK_ENV_ID}",
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.archive_environment(MOCK_ENV_ID)
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_create_environment_sends_correct_payload(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/environments/defaultEnvironment", json=MOCK_ENVIRONMENT
    )
    create_mock = requests_mock.post(
        f"{dummy_hostname}/api/environments/beta/environments",
        json=MOCK_ENVIRONMENT,
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.create_environment(name="my-env", visibility="Private")
    body = create_mock.last_request.json()
    assert body["name"] == "my-env"
    assert body["visibility"] == "Private"
    assert body["image"] == "ubuntu:20.04"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_create_environment_with_explicit_base_image(requests_mock, dummy_hostname):
    create_mock = requests_mock.post(
        f"{dummy_hostname}/api/environments/beta/environments",
        json=MOCK_ENVIRONMENT,
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.create_environment(name="my-env", visibility="Private", base_image="python:3.11")
    body = create_mock.last_request.json()
    assert body["image"] == "python:3.11"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_useable_environments_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/useableEnvironments",
        json={"environments": [MOCK_ENVIRONMENT]},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d._useable_environments_list()
    assert isinstance(result, list)
    assert result[0]["id"] == MOCK_ENV_ID


# ---------------------------------------------------------------------------
# Integration tests (require a live Domino deployment)
# ---------------------------------------------------------------------------


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
