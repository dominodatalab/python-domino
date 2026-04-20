"""
Tests for the runs/jobs API (v1 runs API and v4 jobs API).
Unit tests at top (no live Domino deployment required).
Integration tests below (skipped unless a live deployment is reachable).
"""
import time
from pprint import pformat

import polling2
import pytest
from requests.exceptions import RequestException

from domino import Domino
from domino import exceptions
from domino.helpers import domino_is_reachable

# Realistic mock IDs used in unit tests.
# Domino IDs (project, job, user) are 24-character hex MongoDB ObjectIds.
# Commit IDs are Git SHA strings.
MOCK_PROJECT_ID = "aabbccddeeff001122334454"
MOCK_JOB_ID = "aabbccddeeff001122334455"
MOCK_RUN_ID = "aabbccddeeff001122334457"
MOCK_USER_ID = "aabbccddeeff001122334456"
MOCK_INPUT_COMMIT_ID = "aabbcc112233"
MOCK_OUTPUT_COMMIT_ID = "ddeeff445566"

# Realistic mock response body from GET /v4/jobs/{id} for a completed job.
MOCK_JOB_RESPONSE_COMPLETED = {
    "id": MOCK_JOB_ID,
    "number": 42,
    "projectId": MOCK_PROJECT_ID,
    "title": None,
    "jobRunCommand": "foo.py",
    "statuses": {
        "isCompleted": True,
        "isArchived": False,
        "isScheduled": False,
        "executionStatus": "Succeeded",
    },
    "stageTime": {
        "submissionTime": 1700000000000,
        "runStartTime": 1700000005000,
        "completedTime": 1700000060000,
    },
    "startedBy": {"id": MOCK_USER_ID, "username": "anyuser"},
    "commitDetails": {
        "inputCommitId": MOCK_INPUT_COMMIT_ID,
        "outputCommitId": MOCK_OUTPUT_COMMIT_ID,
    },
}

# Minimal run mock responses for v1 API unit tests.
MOCK_RUN_QUEUED = {
    "id": MOCK_RUN_ID,
    "status": "Queued",
    "commitId": "abc123",
}

MOCK_RUN_SUCCEEDED = {
    "id": MOCK_RUN_ID,
    "status": "Succeeded",
    "commitId": "abc123",
}

# Minimal job response for simple v4 unit tests.
MOCK_JOB_RESPONSE_SIMPLE = {
    "id": MOCK_JOB_ID,
    "statuses": {
        "isCompleted": True,
        "executionStatus": "Succeeded",
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
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/hardwareTiers", json=[]
    )
    yield


@pytest.fixture
def mock_job_start_blocking_setup(requests_mock, dummy_hostname):
    """
    Mocks all API calls made internally by job_start_blocking() so those
    tests can run without a live deployment.
    """
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})

    project_endpoint = "v4/gateway/projects/findProjectByOwnerAndName"
    project_query = "ownerName=anyuser&projectName=anyproject"
    requests_mock.get(
        f"{dummy_hostname}/{project_endpoint}?{project_query}", json={"id": MOCK_PROJECT_ID}
    )

    requests_mock.post(
        f"{dummy_hostname}/v4/jobs/start",
        json={
            "id": MOCK_JOB_ID,
            "number": 42,
            "projectId": MOCK_PROJECT_ID,
            "title": None,
            "jobRunCommand": "foo.py",
            "statuses": {
                "isCompleted": False,
                "isArchived": False,
                "isScheduled": False,
                "executionStatus": "Queued",
            },
            "queuedJobHistoryDetails": {
                "expectedWait": "< 1 minute",
                "explanation": "Resources are available",
                "helpText": None,
            },
            "stageTime": {
                "submissionTime": 1700000000000,
                "runStartTime": None,
                "completedTime": None,
            },
            "startedBy": {"id": MOCK_USER_ID, "username": "anyuser"},
            "commitDetails": {
                "inputCommitId": MOCK_INPUT_COMMIT_ID,
                "outputCommitId": None,
            },
        },
    )

    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/run/{MOCK_JOB_ID}/stdout",
        json={"stdout": "whatever"},
    )

    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/hardwareTiers", json=[]
    )
    yield


# ---------------------------------------------------------------------------
# Unit tests — v1 Runs API
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_runs_list_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
        json={"objectType": "list", "data": [MOCK_RUN_QUEUED]},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.runs_list()
    assert result["objectType"] == "list"
    assert isinstance(result["data"], list)


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_runs_start_returns_json(requests_mock, dummy_hostname):
    requests_mock.post(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
        json=MOCK_RUN_QUEUED,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.runs_start(["main.py"])
    assert result["id"] == MOCK_RUN_ID
    assert result["status"] == "Queued"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_runs_start_sends_correct_payload(requests_mock, dummy_hostname):
    requests_mock.post(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
        json=MOCK_RUN_QUEUED,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.runs_start(["main.py"], isDirect=True, commitId="abc123", title="test run")
    body = requests_mock.last_request.json()
    assert body["isDirect"] is True
    assert body["commitId"] == "abc123"
    assert body["title"] == "test run"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_runs_start_reraises_relogin_exception(requests_mock, dummy_hostname):
    requests_mock.post(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs",
        status_code=403,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.request_manager.post = lambda *a, **kw: (_ for _ in ()).throw(
        exceptions.ReloginRequiredException("relogin required")
    )
    with pytest.raises(exceptions.ReloginRequiredException):
        d.runs_start(["main.py"])


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_runs_status_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/runs/{MOCK_RUN_ID}",
        json=MOCK_RUN_SUCCEEDED,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.runs_status(MOCK_RUN_ID)
    assert result["status"] == "Succeeded"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_runs_stdout_returns_string(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/run/{MOCK_RUN_ID}/stdout",
        json={"stdout": "Hello from the run"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.runs_stdout(MOCK_RUN_ID)
    assert "Hello from the run" in result


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_run_log_excludes_setup_when_false(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/run/{MOCK_RUN_ID}/stdout",
        json={"stdout": "stdout output", "setup": "setup output"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_run_log(MOCK_RUN_ID, includeSetupLog=False)
    assert "stdout output" in result
    assert "setup output" not in result


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_run_log_includes_setup_by_default(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/run/{MOCK_RUN_ID}/stdout",
        json={"stdout": "stdout output", "setup": "setup output"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_run_log(MOCK_RUN_ID)
    assert "stdout output" in result
    assert "setup output" in result


# ---------------------------------------------------------------------------
# Unit tests — v4 Jobs API
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_job_start_reraises_relogin_exception(dummy_hostname):
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.request_manager.post = lambda *a, **kw: (_ for _ in ()).throw(
        exceptions.ReloginRequiredException("relogin required")
    )
    with pytest.raises(exceptions.ReloginRequiredException):
        d.job_start("main.py")


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_job_stop_sends_correct_payload(requests_mock, dummy_hostname):
    stop_mock = requests_mock.post(f"{dummy_hostname}/v4/jobs/stop", status_code=200)
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.job_stop(MOCK_JOB_ID, commit_results=False)
    body = stop_mock.last_request.json()
    assert body["jobId"] == MOCK_JOB_ID
    assert body["commitResults"] is False


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_job_stop_defaults_commit_results_true(requests_mock, dummy_hostname):
    stop_mock = requests_mock.post(f"{dummy_hostname}/v4/jobs/stop", status_code=200)
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.job_stop(MOCK_JOB_ID)
    body = stop_mock.last_request.json()
    assert body["commitResults"] is True


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_job_restart_sends_correct_payload(requests_mock, dummy_hostname):
    restart_mock = requests_mock.post(
        f"{dummy_hostname}/v4/jobs/restart", json=MOCK_JOB_RESPONSE_SIMPLE, status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.job_restart(MOCK_JOB_ID)
    body = restart_mock.last_request.json()
    assert body["jobId"] == MOCK_JOB_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_job_runtime_execution_details_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/jobs/{MOCK_JOB_ID}/runtimeExecutionDetails",
        json={"hardwareTier": {"id": "small-k8s"}},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.job_runtime_execution_details(MOCK_JOB_ID)
    assert result["hardwareTier"]["id"] == "small-k8s"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_jobs_list_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/jobs",
        json={"jobs": [MOCK_JOB_RESPONSE_SIMPLE]},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.jobs_list(project_id=MOCK_PROJECT_ID)
    assert "jobs" in result


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_hardware_tiers_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/hardwareTiers",
        json=[{"hardwareTier": {"id": "small-k8s", "name": "Small"}}],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.hardware_tiers_list()
    assert isinstance(result, list)
    assert result[0]["hardwareTier"]["id"] == "small-k8s"


# ---------------------------------------------------------------------------
# Unit tests — job_start_blocking
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clear_token_file_from_env", "mock_job_start_blocking_setup")
def test_job_status_completes_with_default_params(requests_mock, dummy_hostname):
    """
    Confirm that the happy path default case passes (no exceptions thrown)
    """
    requests_mock.get(
        f"{dummy_hostname}/v4/jobs/{MOCK_JOB_ID}",
        json=MOCK_JOB_RESPONSE_COMPLETED,
    )

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    job_status = d.job_start_blocking(command="foo.py", poll_freq=1, max_poll_time=1)
    assert job_status["statuses"]["isCompleted"] is True


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_job_start_blocking_setup")
def test_job_start_sends_main_repo_git_ref(requests_mock, dummy_hostname):
    """
    Confirm that main_repo_git_ref is passed through to the jobs/start request body.
    """
    requests_mock.get(
        f"{dummy_hostname}/v4/jobs/{MOCK_JOB_ID}",
        json=MOCK_JOB_RESPONSE_COMPLETED,
    )

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    git_ref = {"type": "branches", "value": "my-feature-branch"}
    d.job_start_blocking(
        command="foo.py",
        main_repo_git_ref=git_ref,
        poll_freq=1,
        max_poll_time=1,
    )

    jobs_start_request = next(
        req for req in requests_mock.request_history
        if req.path == "/v4/jobs/start"
    )
    assert jobs_start_request.json()["mainRepoGitRef"] == git_ref


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_job_start_blocking_setup")
def test_job_status_ignores_RequestException_and_times_out(
    requests_mock, dummy_hostname
):
    """
    Test that the default behavior is to simply ignore RequestException being thrown.
    (In this case, timing out via polling2.TimeoutException is expected.)
    """
    requests_mock.get(f"{dummy_hostname}/v4/jobs/{MOCK_JOB_ID}", exc=RequestException)

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    with pytest.raises(polling2.TimeoutException):
        d.job_start_blocking(command="foo.py", poll_freq=1, max_poll_time=1)


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_job_start_blocking_setup")
def test_job_status_without_ignoring_exceptions(requests_mock, dummy_hostname):
    """
    Test that ignore_exceptions can be overridden by passing in an empty tuple.
    The call should fail immediately with RequestException.
    """
    requests_mock.get(f"{dummy_hostname}/v4/jobs/{MOCK_JOB_ID}", exc=RequestException)

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    with pytest.raises(RequestException):
        d.job_start_blocking(command="foo.py", ignore_exceptions=())


# ---------------------------------------------------------------------------
# Integration tests (require a live Domino deployment)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_job_start_blocking(default_domino_client):
    """
    Confirm that we can start a job using the v4 API, and block until it succeeds.
    """
    job = default_domino_client.job_start_blocking(command="main.py")
    assert job["statuses"]["executionStatus"] == "Succeeded"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_job_start_override_hardware_tier_id(default_domino_client):
    """
    Confirm that we can start a job using the v4 API and override the hardware tier id
    """
    hardware_tiers = default_domino_client.hardware_tiers_list()
    non_default_hardware_tiers = [
        hwt for hwt in hardware_tiers if not hwt["hardwareTier"]["hwtFlags"]["isDefault"]
    ]
    if len(non_default_hardware_tiers) == 0:
        pytest.xfail("No non-default hardware tiers found: cannot run test")

    override_hardware_tier_id = non_default_hardware_tiers[0]["hardwareTier"]["id"]
    job_status = default_domino_client.job_start_blocking(
        command="main.py", hardware_tier_id=override_hardware_tier_id
    )
    assert job_status["statuses"]["isCompleted"] is True
    job_red = default_domino_client.job_runtime_execution_details(job_status["id"])
    assert job_red["hardwareTier"]["id"] == override_hardware_tier_id


# deprecated but ensuring it still works for now
@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_job_start_override_hardware_tier_name(default_domino_client):
    """
    Confirm that we can start a job using the v4 API and override the hardware tier via hardware_tier_name
    """
    hardware_tiers = default_domino_client.hardware_tiers_list()

    non_default_hardware_tiers = [
        hwt for hwt in hardware_tiers if not hwt["hardwareTier"]["hwtFlags"]["isDefault"]
    ]
    if len(non_default_hardware_tiers) == 0:
        pytest.xfail("No non-default hardware tiers found: cannot run test")

    override_hardware_tier_name = non_default_hardware_tiers[0]["hardwareTier"]["name"]
    job_status = default_domino_client.job_start_blocking(
        command="main.py", hardware_tier_name=override_hardware_tier_name
    )

    assert job_status["statuses"]["isCompleted"] is True
    job_red = default_domino_client.job_runtime_execution_details(job_status["id"])
    assert job_red["hardwareTier"]["name"] == override_hardware_tier_name


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_runs_list(default_domino_client):
    """
    Confirm that the v1 API endpoint to list jobs returns a list.
    """
    runs = default_domino_client.runs_list()
    assert (
        runs["objectType"] == "list"
    ), f"runs_list returned unexpected result:\n{pformat(runs)}"
    assert isinstance(
        runs["data"], list
    ), f"runs_list returned unexpected result:\n{pformat(runs)}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_queue_job(default_domino_client):
    """
    Queue a job, and then poll until the job completes (timeout at 240 seconds).
    """
    job = default_domino_client.job_start("main.py")

    remaining_polling_seconds = 240
    while remaining_polling_seconds > 0:
        job_status = default_domino_client.job_status(job["id"])
        if not job_status["statuses"]["isCompleted"]:
            time.sleep(3)
            remaining_polling_seconds -= 3
            print(f"Job {job['id']} has not completed.")
            continue

        exec_status = job_status["statuses"]["executionStatus"]
        try:
            assert exec_status == "Succeeded"
            print(f"Job {job['id']} succeeded.")
            break
        except AssertionError:
            print(f"Job failed: {pformat(job_status)}")
            raise
    else:
        pytest.fail(f"Job took too long to complete: {pformat(job_status)}")


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_job_result_stdout(default_domino_client):
    """
    Queue a job, and then poll until the job completes (timeout at 240 seconds).
    """
    job = default_domino_client.job_start("main.py")

    remaining_polling_seconds = 240
    while remaining_polling_seconds > 0:
        job_status = default_domino_client.job_status(job["id"])
        if not job_status["statuses"]["isCompleted"]:
            time.sleep(5)
            remaining_polling_seconds -= 5
            continue

        stdout_data = default_domino_client.runs_stdout(job["id"])

        try:
            html_start_tags = "<pre style='white-space: pre-wrap; white-space"
            assert stdout_data != ""
            assert html_start_tags not in stdout_data
            break
        except AssertionError:
            print(f"Job failed: {pformat(job_status)}")
            raise
    else:
        pytest.fail(f"Job took too long to complete: {pformat(job_status)}")
