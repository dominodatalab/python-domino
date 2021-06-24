import polling2
import pytest

from domino import Domino
from requests.exceptions import RequestException


@pytest.fixture
def dummy_hostname():
    return "http://domino.somefakecompany.com"


@pytest.fixture
def mock_job_start_blocking_setup(requests_mock, dummy_hostname):
    """
    Create mock replies to the chain of calls required before checking job status
    """
    # Mock the /version API endpoint (GET)
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})

    # Mock /findProjectByOwnerAndName API endpoint  (GET)
    project_endpoint = "v4/gateway/projects/findProjectByOwnerAndName"
    project_query = "ownerName=anyuser&projectName=anyproject"
    requests_mock.get(f"{dummy_hostname}/{project_endpoint}?{project_query}", json={})

    # Mock the jobs/start API endpoint (POST) and return run with ID 123
    jobs_start_endpoint = "v4/jobs/start"
    requests_mock.post(f"{dummy_hostname}/{jobs_start_endpoint}", json={"id": "123"})

    # Mock STDOUT for run with ID 123
    stdout_endpoint = "v1/projects/anyuser/anyproject/run/123/stdout"
    requests_mock.get(f"{dummy_hostname}/{stdout_endpoint}", json={"stdout": "whatever"})

    yield


@pytest.mark.usefixtures("clear_env_for_api_key_test", "mock_job_start_blocking_setup")
def test_job_status_completes_with_default_params(requests_mock, dummy_hostname):
    """
    Confirm that the happy path default case passes (no exceptions thrown)
    """
    # Mock a typical response from the jobs status API endpoint (GET)
    jobs_status_endpoint = "v4/jobs/123"
    requests_mock.get(f"{dummy_hostname}/{jobs_status_endpoint}",
                      json={"statuses": {"isCompleted": True, "executionStatus": "whatever"}})

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    job_status = d.job_start_blocking(command="foo.py", poll_freq=1, max_poll_time=1)
    assert job_status['statuses']['isCompleted'] is True


@pytest.mark.usefixtures("clear_env_for_api_key_test", "mock_job_start_blocking_setup")
def test_job_status_ignores_RequestException_and_times_out(requests_mock, dummy_hostname):
    """
    Test that the default behavior is to simply ignore RequestException being thrown.
    (In this case, timing out via polling2.TimeoutException is expected.)
    """
    # Force the jobs status API endpoint to throw a RequestException when called
    jobs_status_endpoint = "v4/jobs/123"
    requests_mock.get(f"{dummy_hostname}/{jobs_status_endpoint}", exc=RequestException)

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    with pytest.raises(polling2.TimeoutException):
        d.job_start_blocking(command="foo.py", poll_freq=1, max_poll_time=1)


@pytest.mark.usefixtures("clear_env_for_api_key_test", "mock_job_start_blocking_setup")
def test_job_status_without_ignoring_exceptions(requests_mock, dummy_hostname):
    """
    Test that ignore_exceptions can be overridden by passing in an empty tuple.
    The call should fail immediately with RequestException.
    """
    # Force the jobs status API endpoint to throw a RequestException when called
    jobs_status_endpoint = "v4/jobs/123"
    requests_mock.get(f"{dummy_hostname}/{jobs_status_endpoint}", exc=RequestException)

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    with pytest.raises(RequestException):
        d.job_start_blocking(command="foo.py", ignore_exceptions=())
