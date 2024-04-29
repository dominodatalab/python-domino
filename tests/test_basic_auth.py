import os

import pytest
import requests

import domino.authentication
from domino import Domino, authentication
from domino.constants import (
    DOMINO_HOST_KEY_NAME,
    DOMINO_TOKEN_FILE_KEY_NAME,
    DOMINO_USER_API_KEY_KEY_NAME,
)
from domino.helpers import domino_is_reachable


@pytest.mark.usefixtures("clear_api_key_from_env", "clear_token_file_from_env")
def test_no_auth_type_error():
    """
    Confirm that trying to instantiate a Domino object with no auth raises
    an AssertionError with the expected error message.
    """
    dummy_host = "http://domino.somefakecompany.com"

    with pytest.raises(RuntimeError):
        Domino(host=dummy_host, project="anyuser/quick-start")


def test_invalid_token_file_error():
    """
    Confirm that trying to instantiate a Domino object with an invalid token file
    raises a FileNotFoundError exception.
    """
    dummy_host = "http://domino.somefakecompany.com"
    invalid_file = "non_existent_token_file.txt"

    with pytest.raises(FileNotFoundError):
        test_domino = Domino(
            host=dummy_host,
            project="anyuser/quick-start",
            domino_token_file=invalid_file,
        )
        test_domino.runs_list()["data"]


def test_malformed_project_input_error(caplog):
    """
    Confirm that passing in a project name without the user name raises a ValueError.
    """
    # This test uses the provided pytest fixture, caplog. For more info, see:
    # https://docs.pytest.org/en/6.2.x/reference.html?highlight=caplog#std-fixture-caplog
    dummy_host = "http://domino.somefakecompany.com"
    invalid_project = "user_project_name"

    with pytest.raises(ValueError):
        Domino(host=dummy_host, project=invalid_project)

    err_msg = f"{invalid_project} must be given in the form username/projectname"
    assert any(
        err_msg in rec.message for rec in caplog.records
    ), f"Expected: {err_msg}, got {caplog.records}"


@pytest.mark.usefixtures("mock_domino_version_response")
def test_object_creation_with_auth_token():
    """
    Confirm that the expected auth type is used when using an auth token.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_auth_token = "top_secret_auth_token"

    d = Domino(
        host=dummy_host, project="anyuser/quick-start", auth_token=dummy_auth_token
    )
    assert isinstance(
        d.request_manager.auth, authentication.BearerAuth
    ), "Authentication using auth_token should be of type authentication.BearerAuth"


@pytest.mark.usefixtures("mock_domino_version_response", "clear_token_file_from_env")
def test_object_creation_with_api_key():
    """
    Confirm that the expected auth type is used when using an api key.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_api_key = "top_secret_api_key"

    d = Domino(host=dummy_host, project="anyuser/quick-start", api_key=dummy_api_key)
    assert isinstance(
        d.request_manager.auth, requests.auth.HTTPBasicAuth
    ), "Authentication using API key should be of type requests.auth.HTTPBasicAuth"


@pytest.mark.usefixtures("mock_domino_version_response", "clear_token_file_from_env", "mock_proxy_response")
def test_object_creation_with_api_proxy():
    """
    Confirm that the expected auth type is used when using api proxy.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_api_proxy = "localhost:1234"

    d = Domino(host=dummy_host, project="anyuser/quick-start", api_proxy=dummy_api_proxy)
    assert isinstance(
        d.request_manager.auth, domino.authentication.ProxyAuth
    ), "Authentication using API proxy should be of type domino.authentication.ProxyAuth"
    assert d.request_manager.auth.api_proxy == "http://localhost:1234"

@pytest.mark.usefixtures("mock_domino_version_response", "clear_token_file_from_env", "mock_proxy_response_https")
def test_object_creation_with_api_proxy_with_scheme():
    """
    Confirm that the expected auth type is used when using api proxy.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_api_proxy = "https://localhost:1234"

    d = Domino(host=dummy_host, project="anyuser/quick-start", api_proxy=dummy_api_proxy)
    assert isinstance(
        d.request_manager.auth, domino.authentication.ProxyAuth
    ), "Authentication using API proxy should be of type domino.authentication.ProxyAuth"
    assert d.request_manager.auth.api_proxy == "https://localhost:1234"


@pytest.mark.usefixtures("mock_domino_version_response")
def test_object_creation_with_token_file(dummy_token_file):
    """
    Confirm that the expected auth type is used when using a token file.
    """
    dummy_host = "http://domino.somefakecompany.com"

    d = Domino(
        host=dummy_host,
        project="anyuser/quick-start",
        domino_token_file=dummy_token_file,
    )
    assert isinstance(
        d.request_manager.auth, authentication.BearerAuth
    ), "Authentication using token_file should be of type authentication.BearerAuth"


@pytest.mark.usefixtures("mock_domino_version_response", "clear_token_file_from_env")
def test_re_authentication_with_a_new_type(dummy_token_file):
    """
    Confirm that the client can re-authenticate with a new authentication token,
    or (in this case) even switch to an API key.
    """
    dummy_host = "http://domino.somefakecompany.com"

    d = Domino(
        host=dummy_host,
        project="anyuser/quick-start",
        domino_token_file=dummy_token_file,
    )
    assert isinstance(
        d.request_manager.auth, authentication.BearerAuth
    ), "Authentication using token_file should be of type authentication.BearerAuth"

    d.authenticate(api_key="bogus_api_key")
    assert isinstance(
        d.request_manager.auth, requests.auth.HTTPBasicAuth
    ), "Re-authentication with API key should be of type requests.auth.HTTPBasicAuth"


@pytest.mark.usefixtures("mock_domino_version_response")
def test_auth_token_precedence():
    """
    Confirm that auth token takes precedence over both token file and API key authentication.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_auth_token = "top_secret_auth_token"
    invalid_token_file = "non_existent_token_file.txt"
    dummy_api_key = "top_secret_api_key"

    d = Domino(
        host=dummy_host,
        project="anyuser/quick-start",
        auth_token=dummy_auth_token,
        domino_token_file=invalid_token_file,
        api_key=dummy_api_key,
    )
    assert isinstance(
        d.request_manager.auth, authentication.BearerAuth
    ), "With multiple authentication options, auth_token string should take highest precendence"


@pytest.mark.usefixtures("mock_domino_version_response")
@pytest.mark.skipif(
    not os.getenv(DOMINO_TOKEN_FILE_KEY_NAME), reason="No token file in environment"
)  # noqa:E501
def test_auth_with_api_key_and_env_token_file():
    """
    Confirm that api key takes precedence over both token file and API key authentication
    if they are not passed as parameters.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_api_key = "top_secret_api_key"

    d = Domino(host=dummy_host, project="anyuser/quick-start", api_key=dummy_api_key)
    assert isinstance(
        d.request_manager.auth, requests.auth.HTTPBasicAuth
    ), "With only api key passed as a parameter, it takes precedence over DOMINO_TOKEN_FILE_KEY_NAME"


@pytest.mark.usefixtures("mock_domino_version_response")
def test_token_file_precedence(dummy_token_file):
    """
    Confirm that token file authentication takes precedence over API key authentication.
    """
    dummy_host = "http://domino.somefakecompany.com"
    dummy_api_key = "top_secret_api_key"

    d = Domino(
        host=dummy_host,
        project="anyuser/quick-start",
        domino_token_file=dummy_token_file,
        api_key=dummy_api_key,
    )
    assert isinstance(
        d.request_manager.auth, authentication.BearerAuth
    ), "When a token file and API are present, auth by token file should take highest precendence"


@pytest.mark.usefixtures("clear_token_file_from_env")
@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@pytest.mark.skipif(
    not os.getenv(DOMINO_USER_API_KEY_KEY_NAME), reason="No API key in environment"
)  # noqa:E501
def test_auth_against_real_deployment_with_api_key():
    """
    Confirm against a live system that validating by API key works.

    Assumes that ${DOMINO_API_HOST} contains a valid Domino URL
    Assumes that ${DOMINO_USER_API_KEY} contains a valid API key
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    api_key = os.getenv(DOMINO_USER_API_KEY_KEY_NAME)

    d = Domino(host=host, project="anyuser/quick-start", api_key=api_key)
    assert isinstance(
        d.request_manager.auth, requests.auth.HTTPBasicAuth
    ), "Authentication using API key should be of type requests.auth.HTTPBasicAuth"

    # Raises a requests.exceptions.HTTPError if authentication failed
    d.environments_list()


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@pytest.mark.skipif(
    not os.getenv(DOMINO_TOKEN_FILE_KEY_NAME), reason="No token file in environment"
)  # noqa:E501
def test_auth_against_real_deployment_with_token_file():
    """
    Confirm against a live system that validating by token file works.

    Assumes that ${DOMINO_API_HOST} contains a valid Domino URL
    Assumes that ${DOMINO_TOKEN_FILE} is a path to a file that contains a valid token
    """
    host = os.getenv(DOMINO_HOST_KEY_NAME)
    token_file = os.getenv(DOMINO_TOKEN_FILE_KEY_NAME)

    d = Domino(host=host, project="anyuser/quick-start", domino_token_file=token_file)
    assert isinstance(
        d.request_manager.auth, authentication.BearerAuth
    ), "Authentication using token_file should be of type authentication.BearerAuth"

    # Raises a requests.exceptions.HTTPError if authentication failed
    d.environments_list()
