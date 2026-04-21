"""
Tests confirming that renamed camelCase parameters emit DeprecationWarning
and that the call still succeeds with the old name.
"""
import pytest

from domino import Domino

MOCK_PROJECT_ID = "aabbccddeeff001122334454"
MOCK_RUN_ID = "aabbccddeeff001122334455"
MOCK_APP_ID = "aabbccddeeff001122334457"
MOCK_COMMIT_ID = "aabbcc112233"


@pytest.fixture
def client(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    return Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")


# ---------------------------------------------------------------------------
# runs_start
# ---------------------------------------------------------------------------

class TestRunsStartDeprecations:
    @pytest.fixture(autouse=True)
    def mock_runs_start(self, requests_mock, dummy_hostname):
        requests_mock.post(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
            json={"runId": MOCK_RUN_ID},
        )

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_isDirect_warns(self, client):
        with pytest.warns(DeprecationWarning, match="isDirect is deprecated"):
            client.runs_start("main.py", isDirect=True)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_commitId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="commitId is deprecated"):
            client.runs_start("main.py", commitId=MOCK_COMMIT_ID)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_publishApiEndpoint_warns(self, client):
        with pytest.warns(DeprecationWarning, match="publishApiEndpoint is deprecated"):
            client.runs_start("main.py", publishApiEndpoint=True)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_new_names_accepted_without_warning(self, client, recwarn):
        client.runs_start("main.py", is_direct=True, commit_id=MOCK_COMMIT_ID)
        deprecation_warnings = [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)
                                and "deprecated" in str(w.message).lower()
                                and any(x in str(w.message) for x in ["isDirect", "commitId"])]
        assert len(deprecation_warnings) == 0


# ---------------------------------------------------------------------------
# runs_start_blocking (spot-check one param — same shim logic)
# ---------------------------------------------------------------------------

class TestRunsStartBlockingDeprecations:
    @pytest.fixture(autouse=True)
    def mock_endpoints(self, requests_mock, dummy_hostname):
        requests_mock.post(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
            json={"runId": MOCK_RUN_ID, "outputCommitId": MOCK_COMMIT_ID, "status": "Succeeded"},
        )
        requests_mock.get(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
            json={"data": [{"id": MOCK_RUN_ID, "outputCommitId": MOCK_COMMIT_ID, "status": "Succeeded"}]},
        )
        requests_mock.get(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/run/{MOCK_RUN_ID}/stdout",
            json={"setup": "", "stdout": "done"},
        )

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_isDirect_warns(self, client):
        with pytest.warns(DeprecationWarning, match="isDirect is deprecated"):
            client.runs_start_blocking("main.py", isDirect=True, poll_freq=1, max_poll_time=5)


# ---------------------------------------------------------------------------
# run_stop / runs_status / get_run_log / runs_stdout
# ---------------------------------------------------------------------------

class TestLegacyRunMethodDeprecations:
    @pytest.fixture(autouse=True)
    def mock_run_endpoints(self, requests_mock, dummy_hostname):
        requests_mock.get(
            f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
            "?ownerName=anyuser&projectName=anyproject",
            json={"id": MOCK_PROJECT_ID},
        )
        requests_mock.post(f"{dummy_hostname}/v4/jobs/stop", json={})
        requests_mock.get(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs/{MOCK_RUN_ID}",
            json={"id": MOCK_RUN_ID, "status": "Succeeded"},
        )
        requests_mock.get(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/run/{MOCK_RUN_ID}/stdout",
            json={"setup": "setup log", "stdout": "hello"},
        )

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_run_stop_runId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="runId is deprecated"):
            client.run_stop(runId=MOCK_RUN_ID)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_run_stop_saveChanges_warns(self, client):
        with pytest.warns(DeprecationWarning, match="saveChanges is deprecated"):
            client.run_stop(run_id=MOCK_RUN_ID, saveChanges=False)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_runs_status_runId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="runId is deprecated"):
            client.runs_status(runId=MOCK_RUN_ID)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_get_run_log_runId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="runId is deprecated"):
            client.get_run_log(runId=MOCK_RUN_ID)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_get_run_log_includeSetupLog_warns(self, client):
        with pytest.warns(DeprecationWarning, match="includeSetupLog is deprecated"):
            client.get_run_log(run_id=MOCK_RUN_ID, includeSetupLog=False)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_runs_stdout_runId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="runId is deprecated"):
            client.runs_stdout(runId=MOCK_RUN_ID)


# ---------------------------------------------------------------------------
# files_list
# ---------------------------------------------------------------------------

class TestFilesListDeprecations:
    @pytest.fixture(autouse=True)
    def mock_files_list(self, requests_mock, dummy_hostname):
        requests_mock.get(
            f"{dummy_hostname}/v1/projects/anyuser/anyproject/files/{MOCK_COMMIT_ID}//",
            json={"data": []},
        )

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_commitId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="commitId is deprecated"):
            client.files_list(commitId=MOCK_COMMIT_ID)


# ---------------------------------------------------------------------------
# endpoint_publish
# ---------------------------------------------------------------------------

class TestEndpointPublishDeprecations:
    @pytest.fixture(autouse=True)
    def mock_endpoint_publish(self, requests_mock, dummy_hostname):
        requests_mock.post(
            f"{dummy_hostname}/v1/anyuser/anyproject/endpoint/publishRelease",
            json={},
        )

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_commitId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="commitId is deprecated"):
            client.endpoint_publish("app.py", "predict", commitId=MOCK_COMMIT_ID)


# ---------------------------------------------------------------------------
# app_publish / app_unpublish
# ---------------------------------------------------------------------------

class TestAppDeprecations:
    @pytest.fixture(autouse=True)
    def mock_app_endpoints(self, requests_mock, dummy_hostname):
        requests_mock.get(
            f"{dummy_hostname}/v4/modelproducts/{MOCK_APP_ID}",
            json={"id": MOCK_APP_ID, "status": "Stopped"},
        )
        requests_mock.post(
            f"{dummy_hostname}/v4/modelproducts/{MOCK_APP_ID}/stop",
            json={},
        )
        requests_mock.post(
            f"{dummy_hostname}/v4/modelproducts/{MOCK_APP_ID}/start",
            json={"id": MOCK_APP_ID, "status": "Running"},
        )

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_app_publish_appId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="appId is deprecated"):
            client.app_publish(appId=MOCK_APP_ID)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_app_publish_unpublishRunningApps_warns(self, client):
        with pytest.warns(DeprecationWarning, match="unpublishRunningApps is deprecated"):
            client.app_publish(app_id=MOCK_APP_ID, unpublishRunningApps=True)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_app_publish_commitId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="commitId is deprecated"):
            client.app_publish(app_id=MOCK_APP_ID, commitId=MOCK_COMMIT_ID)

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_app_publish_environmentId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="environmentId is deprecated"):
            client.app_publish(app_id=MOCK_APP_ID, environmentId="env-123")

    @pytest.mark.usefixtures("clear_token_file_from_env")
    def test_app_unpublish_appId_warns(self, client):
        with pytest.warns(DeprecationWarning, match="appId is deprecated"):
            client.app_unpublish(appId=MOCK_APP_ID)
