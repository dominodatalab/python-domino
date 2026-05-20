"""
Unit tests for app publish/unpublish methods.
All tests use requests_mock — no live Domino deployment required.
"""

import pytest

from domino import Domino

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_APP_ID = "aabbccddeeff001122334457"

MOCK_APP = {
    "id": MOCK_APP_ID,
    "status": "Running",
    "projectId": MOCK_PROJECT_ID,
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


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_publish_starts_existing_app(requests_mock, dummy_hostname):
    # app_id: returns existing app
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    # app_unpublish path: get app status
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}", json={"status": "Stopped"}
    )
    # app_start
    requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/start",
        json={"status": "Running"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    response = d.app_publish(unpublishRunningApps=False)
    assert response.status_code == 200


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_publish_creates_app_when_none_exists(requests_mock, dummy_hostname):
    # app_id returns empty list — no app exists
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}", json=[]
    )
    # __app_create
    requests_mock.post(f"{dummy_hostname}/v4/modelProducts", json={"id": MOCK_APP_ID})
    # app_start
    requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/start",
        json={"status": "Running"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    response = d.app_publish(unpublishRunningApps=False)
    assert response.status_code == 200


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_publish_stops_running_app_before_starting(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}", json={"status": "Running"}
    )
    stop_mock = requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/stop", status_code=200
    )
    requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/start",
        json={"status": "Running"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(unpublishRunningApps=True)
    assert stop_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_publish_sends_hardware_tier_and_environment(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}", json={"status": "Stopped"}
    )
    start_mock = requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/start", status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(
        unpublishRunningApps=False,
        hardwareTierId="hw-tier-1",
        environmentId="env-id-1",
    )
    body = start_mock.last_request.json()
    assert body["hardwareTierId"] == "hw-tier-1"
    assert body["environmentId"] == "env-id-1"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_publish_omits_null_fields_from_payload(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}", json={"status": "Stopped"}
    )
    start_mock = requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/start", status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(unpublishRunningApps=False)
    body = start_mock.last_request.json()
    assert "hardwareTierId" not in body
    assert "environmentId" not in body


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_unpublish_stops_running_app(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}", json={"status": "Running"}
    )
    stop_mock = requests_mock.post(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}/stop", status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_unpublish()
    assert stop_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_unpublish_does_nothing_when_no_app_exists(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}", json=[]
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.app_unpublish()
    assert result is None


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_unpublish_does_nothing_when_app_already_stopped(
    requests_mock, dummy_hostname
):
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts/{MOCK_APP_ID}", json={"status": "Stopped"}
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.app_unpublish()
    assert result is None


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_id_returns_id_when_app_exists(requests_mock, dummy_hostname):
    """
    Confirm that the public app_id property returns the ID of the first app
    in the current project.
    """
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_APP],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    assert d.app_id == MOCK_APP_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_app_id_returns_none_when_no_app_exists(requests_mock, dummy_hostname):
    """
    Confirm that the public app_id property returns None when the project
    has no apps.
    """
    requests_mock.get(
        f"{dummy_hostname}/v4/modelProducts?projectId={MOCK_PROJECT_ID}", json=[]
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    assert d.app_id is None
