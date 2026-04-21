import pytest

from domino import Domino

# Realistic mock IDs — 24-character hex MongoDB ObjectIds.
MOCK_PROJECT_ID = "aabbccddeeff001122334454"
MOCK_APP_ID = "aabbccddeeff001122334457"


@pytest.fixture
def mock_app_publish_setup(requests_mock, dummy_hostname):
    """
    Mocks all API calls that app_publish() depends on when an appId is provided.

    If any dependent calls are added to app_publish or app_unpublish, they
    must be mocked here as well.
    """
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})

    # Mock app status lookup (GET) used by app_unpublish via __app_get_status
    requests_mock.get(
        f"{dummy_hostname}/v4/modelproducts/{MOCK_APP_ID}",
        json={"id": MOCK_APP_ID, "status": "Running"},
    )

    # Mock app stop (POST) called by app_unpublish when app is running
    requests_mock.post(
        f"{dummy_hostname}/v4/modelproducts/{MOCK_APP_ID}/stop",
        json={"id": MOCK_APP_ID, "status": "Stopped"},
    )

    # Mock app start (POST) — the main call made by app_publish
    requests_mock.post(
        f"{dummy_hostname}/v4/modelproducts/{MOCK_APP_ID}/start",
        json={"id": MOCK_APP_ID, "status": "Running"},
    )
    yield


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_with_branch(requests_mock, dummy_hostname):
    """
    Confirm that the branch parameter is correctly formatted as mainRepoGitRef
    in the app start request body.
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(appId=MOCK_APP_ID, branch="my-feature-branch")

    app_start_request = next(
        req for req in requests_mock.request_history
        if req.path == f"/v4/modelproducts/{MOCK_APP_ID}/start"
    )
    assert app_start_request.json()["mainRepoGitRef"] == {
        "type": "branches",
        "value": "my-feature-branch",
    }


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_with_commit_id(requests_mock, dummy_hostname):
    """
    Confirm that the commitId parameter is correctly formatted as mainRepoGitRef
    in the app start request body.
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(appId=MOCK_APP_ID, commitId="abc123def456")

    app_start_request = next(
        req for req in requests_mock.request_history
        if req.path == f"/v4/modelproducts/{MOCK_APP_ID}/start"
    )
    assert app_start_request.json()["mainRepoGitRef"] == {
        "type": "commitId",
        "value": "abc123def456",
    }


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_omits_git_ref_when_not_provided(requests_mock, dummy_hostname):
    """
    Confirm that mainRepoGitRef is omitted from the request body when neither
    branch nor commitId is provided.
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(appId=MOCK_APP_ID)

    app_start_request = next(
        req for req in requests_mock.request_history
        if req.path == f"/v4/modelproducts/{MOCK_APP_ID}/start"
    )
    assert "mainRepoGitRef" not in app_start_request.json()


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_raises_if_both_branch_and_commit_id_provided(dummy_hostname):
    """
    Confirm that providing both branch and commitId raises a ValueError.
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(ValueError, match="Only one of commitId or branch"):
        d.app_publish(appId=MOCK_APP_ID, branch="my-branch", commitId="abc123")


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_unpublishes_running_app(requests_mock, dummy_hostname):
    """
    Confirm that app_publish calls stop on the running app before starting
    when unpublishRunningApps=True (the default).
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(appId=MOCK_APP_ID, unpublishRunningApps=True)

    stop_requests = [
        req for req in requests_mock.request_history
        if req.path == f"/v4/modelproducts/{MOCK_APP_ID}/stop"
    ]
    assert len(stop_requests) == 1


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_skips_unpublish_when_disabled(requests_mock, dummy_hostname):
    """
    Confirm that app_publish does not call stop when unpublishRunningApps=False.
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(appId=MOCK_APP_ID, unpublishRunningApps=False)

    stop_requests = [
        req for req in requests_mock.request_history
        if req.path == f"/v4/modelproducts/{MOCK_APP_ID}/stop"
    ]
    assert len(stop_requests) == 0


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_app_publish_setup")
def test_app_publish_targets_specific_app_id(requests_mock, dummy_hostname):
    """
    Confirm that the provided appId is used in the start endpoint URL, not the
    default first-app lookup.
    """
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.app_publish(appId=MOCK_APP_ID)

    start_requests = [
        req for req in requests_mock.request_history
        if req.path == f"/v4/modelproducts/{MOCK_APP_ID}/start"
    ]
    assert len(start_requests) == 1
