"""
Unit tests for collaborator API methods.
All tests use requests_mock — no live Domino deployment required.
"""
import pytest

from domino import Domino
from domino import exceptions

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_USER_ID = "aabbccddeeff001122334460"

MOCK_USER = {
    "id": MOCK_USER_ID,
    "userName": "jdoe",
    "email": "jdoe@example.com",
}


@pytest.fixture
def base_mocks(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID},
    )
    yield


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_collaborators_get_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/anyuser/anyproject/collaborators",
        json=[{"username": "jdoe"}],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.collaborators_get()
    assert isinstance(result, list)
    assert result[0]["username"] == "jdoe"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_user_id_returns_id_by_username(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[MOCK_USER])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_user_id("jdoe")
    assert result == MOCK_USER_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_user_id_returns_id_by_email(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[MOCK_USER])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_user_id("jdoe@example.com")
    assert result == MOCK_USER_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_get_user_id_returns_none_when_not_found(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[MOCK_USER])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.get_user_id("nobody@example.com")
    assert result is None


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_collaborators_add_sends_correct_payload(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[MOCK_USER])
    add_mock = requests_mock.post(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/collaborators",
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.collaborators_add("jdoe")
    body = add_mock.last_request.json()
    assert body["collaboratorId"] == MOCK_USER_ID
    assert body["projectRole"] == "Contributor"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_collaborators_add_raises_when_user_not_found(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.UserNotFoundException):
        d.collaborators_add("nobody")


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_collaborators_remove_sends_delete(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[MOCK_USER])
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/collaborators/{MOCK_USER_ID}",
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.collaborators_remove("jdoe")
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_collaborators_remove_raises_when_user_not_found(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/v4/users", json=[])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.UserNotFoundException):
        d.collaborators_remove("nobody")
