import os

import requests

from domino import Domino, bearer_auth
from domino.constants import (
    DOMINO_HOST_KEY_NAME,
    DOMINO_USER_API_KEY_KEY_NAME,
    DOMINO_TOKEN_FILE_KEY_NAME
)
from domino.helpers import domino_is_reachable
from pytest import mark


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
