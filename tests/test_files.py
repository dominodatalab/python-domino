"""
Unit tests for files_download() convenience method.
All tests use requests_mock — no live Domino deployment required.
"""

import pytest

from domino import Domino

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_COMMIT_ID = "aabbcc112233"
FILE_CONTENT = b"hello world"


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
def test_files_download_with_explicit_commit_id(requests_mock, dummy_hostname):
    """
    Confirm that files_download() uses the provided commit_id and does not
    call commits_list (#24, #31).
    """
    requests_mock.get(
        f"{dummy_hostname}/api/projects/v1/projects/{MOCK_PROJECT_ID}"
        f"/files/{MOCK_COMMIT_ID}//README.md/content",
        content=FILE_CONTENT,
    )

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.files_download("/README.md", commit_id=MOCK_COMMIT_ID)
    assert result.read() == FILE_CONTENT


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_files_download_defaults_to_latest_commit(requests_mock, dummy_hostname):
    """
    Confirm that files_download() fetches the latest commit when commit_id
    is omitted (#24, #31).
    """
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/commits",
        json=[{"id": MOCK_COMMIT_ID}, {"id": "oldercommit"}],
    )
    requests_mock.get(
        f"{dummy_hostname}/api/projects/v1/projects/{MOCK_PROJECT_ID}"
        f"/files/{MOCK_COMMIT_ID}//README.md/content",
        content=FILE_CONTENT,
    )

    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.files_download("/README.md")
    assert result.read() == FILE_CONTENT
