import os

import pytest
import requests_mock

from domino.constants import (
    DOMINO_TOKEN_FILE_KEY_NAME,
    DOMINO_USER_API_KEY_KEY_NAME
)


@pytest.fixture
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
        response = mock_endpoint.get(f"{dummy_url}/version", json=version_info, status_code=200)
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
