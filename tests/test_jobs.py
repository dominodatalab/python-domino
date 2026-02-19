import time
from pprint import pformat

import polling2
import pytest
from requests.exceptions import RequestException

from domino import Domino
from domino.helpers import domino_is_reachable

# Realistic mock IDs used in unit tests.
# Domino IDs (project, job, user) are 24-character hex MongoDB ObjectIds.
# Commit IDs are Git SHA strings.
MOCK_PROJECT_ID = "aabbccddeeff001122334454"
MOCK_JOB_ID = "aabbccddeeff001122334455"
MOCK_USER_ID = "aabbccddeeff001122334456"
MOCK_INPUT_COMMIT_ID = "aabbcc112233"
MOCK_OUTPUT_COMMIT_ID = "ddeeff445566"

# Realistic mock response body from GET /v4/jobs/{id} for a completed job.
# Mirrors a subset of the actual API response schema.
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


@pytest.fixture
def mock_job_start_blocking_setup(requests_mock, dummy_hostname):
    """
    Some of the tests in this file are true unit tests, and do not require
    a live deployment. In order for them to run, any API calls made by
    job_start() internally need to have mocked responses.

    This is the test fixture where all of the mocked API return values are
    created.

    If any dependent calls to the API are added to job_start, then they must
    be mocked here as well.
    """
    # Mock the /version API endpoint (GET)
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})

    # Mock /findProjectByOwnerAndName API endpoint (GET) and return the mock project ID
    project_endpoint = "v4/gateway/projects/findProjectByOwnerAndName"
    project_query = "ownerName=anyuser&projectName=anyproject"
    requests_mock.get(
        f"{dummy_hostname}/{project_endpoint}?{project_query}", json={"id": MOCK_PROJECT_ID}
    )

    # Mock the jobs/start API endpoint (POST) and return a realistic job object
    # representing a newly queued job. Mirrors a subset of the actual API response schema.
    jobs_start_endpoint = "v4/jobs/start"
    requests_mock.post(
        f"{dummy_hostname}/{jobs_start_endpoint}",
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

    # Mock STDOUT for the mock job ID
    stdout_endpoint = f"v1/projects/anyuser/anyproject/run/{MOCK_JOB_ID}/stdout"
    requests_mock.get(
        f"{dummy_hostname}/{stdout_endpoint}", json={"stdout": "whatever"}
    )

    # Mock HWT endpoint
    hwt_endpoint = f"v4/projects/{MOCK_PROJECT_ID}/hardwareTiers"
    requests_mock.get(f"{dummy_hostname}/{hwt_endpoint}", json=[])
    yield


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_job_start_blocking_setup")
def test_job_status_completes_with_default_params(requests_mock, dummy_hostname):
    """
    Confirm that the happy path default case passes (no exceptions thrown)
    """
    # Mock a typical response from the jobs status API endpoint (GET)
    jobs_status_endpoint = f"v4/jobs/{MOCK_JOB_ID}"
    requests_mock.get(
        f"{dummy_hostname}/{jobs_status_endpoint}",
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
    jobs_status_endpoint = f"v4/jobs/{MOCK_JOB_ID}"
    requests_mock.get(
        f"{dummy_hostname}/{jobs_status_endpoint}",
        json=MOCK_JOB_RESPONSE_COMPLETED,
    )

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    git_ref = {"type": "branch", "value": "my-feature-branch"}
    d.job_start_blocking(
        command="foo.py",
        main_repo_git_ref=git_ref,
        poll_freq=1,
        max_poll_time=1,
    )

    # Verify the last request to jobs/start contained the correct mainRepoGitRef
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
    # Force the jobs status API endpoint to throw a RequestException when called
    jobs_status_endpoint = f"v4/jobs/{MOCK_JOB_ID}"
    requests_mock.get(f"{dummy_hostname}/{jobs_status_endpoint}", exc=RequestException)

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    with pytest.raises(polling2.TimeoutException):
        d.job_start_blocking(command="foo.py", poll_freq=1, max_poll_time=1)


@pytest.mark.usefixtures("clear_token_file_from_env", "mock_job_start_blocking_setup")
def test_job_status_without_ignoring_exceptions(requests_mock, dummy_hostname):
    """
    Test that ignore_exceptions can be overridden by passing in an empty tuple.
    The call should fail immediately with RequestException.
    """
    # Force the jobs status API endpoint to throw a RequestException when called
    jobs_status_endpoint = f"v4/jobs/{MOCK_JOB_ID}"
    requests_mock.get(f"{dummy_hostname}/{jobs_status_endpoint}", exc=RequestException)

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    with pytest.raises(RequestException):
        d.job_start_blocking(command="foo.py", ignore_exceptions=())


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
