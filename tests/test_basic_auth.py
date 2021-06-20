import os
import socket
import urllib

import requests
import requests_mock

from domino import Domino, bearer_auth
from domino.constants import (
    DOMINO_HOST_KEY_NAME,
    DOMINO_USER_API_KEY_KEY_NAME,
    DOMINO_TOKEN_FILE_KEY_NAME
)
from pytest import fixture, mark


def domino_is_reachable(url=os.getenv(DOMINO_HOST_KEY_NAME), port="443"):
    """
    Confirm that a deployment is accessible for tests that require it.
    """
    if url is None:
        return False

    fqdn = urllib.parse.urlsplit(url).netloc
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((fqdn, int(port)))
        is_reachable = True
    except OSError:
        print(f"{fqdn}:{port} is not reachable")
        is_reachable = False
    finally:
        s.close()

    return is_reachable


@fixture
def mock_domino_version_response():
    """
    Simulate a valid response to an authenticated /version GET request.

    Assumes the target endpoint is domino.somefakecompany.com/version.
    """
    version_info = {
        "buildId": "12345",
        "buildUrl": "https://server.somefakecompany.com/domino/12345",
        "commitId": "123deadbeef456",
        "commitUrl": "https://repo.somefakecompany.com/domino/commit/123deadbeef456",
        "timestamp": "2021-06-14T16:50:02Z",
        "version": "9.9.9"
    }

    dummy_url = "http://domino.somefakecompany.com"
    with requests_mock.Mocker() as mock_endpoint:
        mock_endpoint.get(f"{dummy_url}/version", json=version_info, status_code=200)
        yield


@fixture
def dummy_token_file(tmpdir):
    """
    Simulate a token file.
    """
    # Refer to https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture for tmpdir usage
    token_file = tmpdir.join("dummy_token_file.txt")
    token_file.write("top_secret_auth_token")
    return token_file


@fixture
def clear_env_for_api_key_test():
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


@mark.usefixtures("mock_domino_version_response", "clear_env_for_api_key_test")
def test_object_creation_with_api_key():
    """
    Confirm that the expected auth type is used when using an api key.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_api_key = "top_secret_api_key"

    d = Domino(host=dummy_host, project="anyuser/quick-start", api_key=dummy_api_key)
    assert isinstance(d.request_manager.auth, requests.auth.HTTPBasicAuth)


@mark.usefixtures("mock_domino_version_response")
def test_object_creation_with_token_file(dummy_token_file):
    """
    Confirm that the expected auth type is used when using a token file.
    """
    dummy_host = "http://domino.somefakecompany.com"

    d = Domino(host=dummy_host, project="anyuser/quick-start", domino_token_file=dummy_token_file)
    assert isinstance(d.request_manager.auth, bearer_auth.BearerAuth)


@mark.usefixtures("clear_env_for_api_key_test")
@mark.skipif(not domino_is_reachable(), reason="No access to a live Domino deployment")
@mark.skipif(not os.getenv(DOMINO_USER_API_KEY_KEY_NAME), reason="No API key in environment")
def test_auth_against_real_deployment_with_api_key():
    """
    Confirm against a live system that validating by API key works.

    Assumes that ${DOMINO_API_HOST} contains a valid Domino URL
    Assumes that ${DOMINO_USER_API_KEY} contains a valid API key
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    api_key = os.getenv(DOMINO_USER_API_KEY_KEY_NAME)

    d = Domino(host=host, project="anyuser/quick-start", api_key=api_key)
    assert isinstance(d.request_manager.auth, requests.auth.HTTPBasicAuth)

    # Raises a requests.exceptions.HTTPError if authentication failed
    d.environments_list()


@mark.skipif(not domino_is_reachable(), reason="No access to a live Domino deployment")
@mark.skipif(not os.getenv(DOMINO_TOKEN_FILE_KEY_NAME), reason="No token file in environment")
def test_auth_against_real_deployment_with_token_file():
    """
    Confirm against a live system that validating by token file works.

    Assumes that ${DOMINO_API_HOST} contains a valid Domino URL
    Assumes that ${DOMINO_TOKEN_FILE} is a path to a file that contains a valid token
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    token_file = os.getenv(DOMINO_TOKEN_FILE_KEY_NAME)

    d = Domino(host=host, project="anyuser/quick-start", domino_token_file=token_file)
    assert isinstance(d.request_manager.auth, bearer_auth.BearerAuth)

    # Raises a requests.exceptions.HTTPError if authentication failed
    d.environments_list()
