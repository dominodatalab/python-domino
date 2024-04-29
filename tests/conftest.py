import os

import pytest
import requests_mock
from requests.auth import AuthBase

from domino import Domino
from domino.constants import (
    DOMINO_HOST_KEY_NAME,
    DOMINO_TOKEN_FILE_KEY_NAME,
    DOMINO_USER_API_KEY_KEY_NAME,
    DOMINO_USER_NAME_KEY_NAME,
)


version_info = {
    "buildId": "12345",
    "buildUrl": "https://server.somefakecompany.com/domino/12345",
    "commitId": "123deadbeef456",
    "commitUrl": "https://repo.somefakecompany.com/domino/commit/123deadbeef456",
    "timestamp": "2021-06-14T16:50:02Z",
    "version": "9.9.9",
}

@pytest.fixture
def dummy_hostname():
    return "http://domino.somefakecompany.com"


@pytest.fixture(scope="module")
def default_domino_client():
    """
    Module-scoped fixture that uses default authentiation, and provides a Domino client object.
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    user = os.getenv(DOMINO_USER_NAME_KEY_NAME)
    assert (
        user
    ), f"User must be specified by {DOMINO_USER_NAME_KEY_NAME} environment variable."
    assert (
        host
    ), f"Host must be specified by {DOMINO_HOST_KEY_NAME} environment variable."

    domino_client = Domino(host=host, project=f"{user}/quick-start")

    # If authentication failed, this raises a requests.exceptions.HTTPError.
    domino_client.environments_list()

    return domino_client


@pytest.fixture(scope="module")
def spark_compute_env_id():
    """
    Module-scoped fixture that uses default authentication, and provides a Domino client object.
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    user = os.getenv(DOMINO_USER_NAME_KEY_NAME)
    assert (
        user
    ), f"User must be specified by {DOMINO_USER_NAME_KEY_NAME} environment variable."
    assert (
        host
    ), f"Host must be specified by {DOMINO_HOST_KEY_NAME} environment variable."

    domino_client = Domino(host=host, project=f"{user}/quick-start")

    env_list = domino_client.environments_list()

    for env in env_list["data"]:
        if "Spark Compute Environment" in env["name"]:
            return env["id"]


@pytest.fixture(scope="module")
def spark_cluster_env_id():
    """
    Module-scoped fixture that uses default authentication, and provides a Domino client object.
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    user = os.getenv(DOMINO_USER_NAME_KEY_NAME)
    assert (
        user
    ), f"User must be specified by {DOMINO_USER_NAME_KEY_NAME} environment variable."
    assert (
        host
    ), f"Host must be specified by {DOMINO_HOST_KEY_NAME} environment variable."

    domino_client = Domino(host=host, project=f"{user}/quick-start")

    env_list = domino_client.environments_list()

    for env in env_list["data"]:
        if "Spark Cluster Environment" in env["name"]:
            return env["id"]


@pytest.fixture
def mock_proxy_response_https():
    """
    Simulate a valid response to an authenticated /version GET request using api proxy with schema
    """

    dummy_url = "https://localhost:1234"
    with requests_mock.Mocker() as mock_endpoint:
        response = mock_endpoint.get(
            f"{dummy_url}/version", json=version_info, status_code=200
        )
        yield response


@pytest.fixture
def mock_proxy_response():
    """
    Simulate a valid response to an authenticated /version GET request using api proxy
    """

    dummy_url = "http://localhost:1234"
    with requests_mock.Mocker() as mock_endpoint:
        response = mock_endpoint.get(
            f"{dummy_url}/version", json=version_info, status_code=200
        )
        yield response



@pytest.fixture
def mock_domino_version_response():
    """
    Simulate a valid response to an authenticated /version GET request.

    Assumes the target endpoint is domino.somefakecompany.com/version.
    """

    dummy_url = "http://domino.somefakecompany.com"
    with requests_mock.Mocker() as mock_endpoint:
        response = mock_endpoint.get(
            f"{dummy_url}/version", json=version_info, status_code=200
        )
        yield response


@pytest.fixture
def dummy_token_file(tmpdir):
    """
    Simulate a token file.
    """
    # Refer to https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture for tmpdir usage
    token_file = tmpdir.join("dummy_token_file.txt")
    token_file.write("top_secret_auth_token")
    return token_file


@pytest.fixture
def clear_token_file_from_env():
    """
    Unset any DOMINO_TOKEN_FILE var from the environment for API key tests.

    If a token file is present in the environment, python-domino uses it preferentially,
    which is mutually incompatible with testing the API key.
    """
    saved_environment = dict(os.environ)
    os.environ.pop(DOMINO_TOKEN_FILE_KEY_NAME, default=None)
    yield

    # Restore original pre-test environment
    os.environ.update(saved_environment)


@pytest.fixture
def clear_api_key_from_env():
    """
    Unset any DOMINO_USER_API_KEY var from the environment.

    If the API key is present in the environment, python-domino uses it automatically,
    which will affect some negative testing.
    """
    saved_environment = dict(os.environ)
    os.environ.pop(DOMINO_USER_API_KEY_KEY_NAME, default=None)
    yield

    # Restore original pre-test environment
    os.environ.update(saved_environment)


@pytest.fixture
def test_auth_base():
    class TestAuth(AuthBase):
        def __init__(self, *args, **kwargs):
            super(TestAuth, self).__init__(*args, **kwargs)
            self.header = None
    return TestAuth()
