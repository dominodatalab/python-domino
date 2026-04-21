"""
Unit tests for the project_id property.
All tests use requests_mock — no live Domino deployment required.
"""
import pytest

from domino import Domino
from domino import exceptions

MOCK_PROJECT_ID = "aabbccddeeff001122334455"


@pytest.fixture
def version_mock(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    yield


@pytest.mark.usefixtures("clear_token_file_from_env", "version_mock")
def test_project_id_returns_id_when_present(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID, "name": "anyproject"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    assert d.project_id == MOCK_PROJECT_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "version_mock")
def test_project_id_raises_when_key_missing(requests_mock, dummy_hostname):
    # __init__ does NOT call project_id, so returning no "id" from the start
    # means the first access in the test body will immediately raise.
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"name": "anyproject"},  # no "id" key
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.ProjectNotFoundException):
        _ = d.project_id


@pytest.mark.usefixtures("clear_token_file_from_env", "version_mock")
def test_project_id_is_cached(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    Domino.project_id.fget.cache_clear()

    # Access multiple times — should only call the API once, served from cache after
    _ = d.project_id
    _ = d.project_id
    _ = d.project_id

    find_calls = [
        r for r in requests_mock.request_history
        if "findProjectByOwnerAndName" in r.url
    ]
    assert len(find_calls) == 1
