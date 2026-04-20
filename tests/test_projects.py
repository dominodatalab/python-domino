"""
Tests for project, file, tag, and commit API methods.
Unit tests at top (no live Domino deployment required).
Integration tests below (skipped unless a live deployment is reachable).
"""
import uuid
import warnings
from pprint import pformat

import pytest

from domino import Domino, exceptions
from domino.exceptions import ProjectNotFoundException
from domino.helpers import domino_is_reachable

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_COMMIT_ID = "aabbccddeeff001122334456"
MOCK_TAG_ID = "aabbccddeeff001122334457"
MOCK_USER_ID = "aabbccddeeff001122334458"

MOCK_PROJECT = {
    "id": MOCK_PROJECT_ID,
    "name": "anyproject",
    "tags": [{"id": MOCK_TAG_ID, "name": "my-tag"}],
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


# ---------------------------------------------------------------------------
# Unit tests (no live Domino deployment required)
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_deployment_version_returns_dict(requests_mock, dummy_hostname):
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.deployment_version()
    assert result["version"] == "9.9.9"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_commits_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/commits",
        json=[MOCK_COMMIT_ID],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.commits_list()
    assert isinstance(result, list)
    assert result[0] == MOCK_COMMIT_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_files_list_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/files/{MOCK_COMMIT_ID}//",
        json={"data": [{"path": "main.py", "key": "abc123"}]},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.files_list(MOCK_COMMIT_ID)
    assert isinstance(result["data"], list)
    assert result["data"][0]["path"] == "main.py"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_files_upload_sends_put(requests_mock, dummy_hostname):
    upload_mock = requests_mock.put(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/test.py",
        json={"path": "test.py"},
        status_code=201,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    import io
    response = d.files_upload("test.py", io.BytesIO(b"print('hello')"))
    assert upload_mock.called
    assert response.status_code == 201


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_files_upload_prepends_slash_if_missing(requests_mock, dummy_hostname):
    upload_mock = requests_mock.put(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/test.py",
        json={"path": "test.py"},
        status_code=201,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    import io
    d.files_upload("test.py", io.BytesIO(b""))
    assert upload_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_blobs_get_returns_content(requests_mock, dummy_hostname):
    blob_key = "a" * 40
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/blobs/{blob_key}",
        content=b"file content here",
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = d.blobs_get(blob_key)
    assert result.read() == b"file content here"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_blobs_get_v2_raises_for_non_canonical_path(requests_mock, dummy_hostname):
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.MalformedInputException):
        d.blobs_get_v2("/domino/mnt/../test.py", MOCK_COMMIT_ID, MOCK_PROJECT_ID)


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_blobs_get_v2_returns_content(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/api/projects/v1/projects/{MOCK_PROJECT_ID}"
        f"/files/{MOCK_COMMIT_ID}/main.py/content",
        content=b"print('hello')",
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.blobs_get_v2("main.py", MOCK_COMMIT_ID, MOCK_PROJECT_ID)
    assert result.read() == b"print('hello')"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_fork_project_sends_correct_payload(requests_mock, dummy_hostname):
    fork_mock = requests_mock.post(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/fork",
        json={"id": "newprojectid", "name": "forked-project"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.fork_project("forked-project")
    assert fork_mock.called
    assert fork_mock.last_request.json()["name"] == "forked-project"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_create_sends_correct_payload(requests_mock, dummy_hostname):
    create_mock = requests_mock.post(
        f"{dummy_hostname}/project",
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.project_create("my-new-project")
    assert create_mock.called
    assert create_mock.last_request.body


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_create_v4_sends_correct_payload(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/api/users",
        json=[{"userName": "anyuser", "id": MOCK_USER_ID}],
    )
    create_mock = requests_mock.post(
        f"{dummy_hostname}/v4/projects",
        json={"id": MOCK_PROJECT_ID, "name": "new-v4-project"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.project_create_v4("new-v4-project", owner_id=MOCK_USER_ID)
    body = create_mock.last_request.json()
    assert body["name"] == "new-v4-project"
    assert body["ownerId"] == MOCK_USER_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_projects_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects",
        json=[MOCK_PROJECT],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.projects_list()
    assert isinstance(result, list)
    assert result[0]["id"] == MOCK_PROJECT_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_tags_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}",
        json=MOCK_PROJECT,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.tags_list()
    assert isinstance(result, list)
    assert result[0]["name"] == "my-tag"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_tags_add_sends_correct_payload(requests_mock, dummy_hostname):
    add_mock = requests_mock.post(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/tags",
        json=[{"id": MOCK_TAG_ID, "name": "new-tag"}],
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.tags_add(["new-tag"])
    assert add_mock.called
    assert add_mock.last_request.json()["tagNames"] == ["new-tag"]


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_tag_details_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/projectTags/{MOCK_TAG_ID}",
        json={"_id": MOCK_TAG_ID, "name": "my-tag"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.tag_details(MOCK_TAG_ID)
    assert result["_id"] == MOCK_TAG_ID
    assert result["name"] == "my-tag"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_tags_remove_sends_delete(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}",
        json=MOCK_PROJECT,
    )
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/tags/{MOCK_TAG_ID}",
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.tags_remove("my-tag")
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_archive_raises_for_nonexistent_project(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects",
        json=[],
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(ProjectNotFoundException):
        d.project_archive("bogus_project")


# ---------------------------------------------------------------------------
# Integration tests (require a live Domino deployment)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_project_create(default_domino_client):
    """
    Confirm that the python-domino client can create a new project.
    """
    new_project_name = f"project-{str(uuid.uuid4())}"
    response = default_domino_client.project_create(new_project_name)
    assert response.status_code == 200, f"{response.status_code}: {response.reason}"

    project_list = default_domino_client.projects_list()
    assert any(
        p["name"] == new_project_name for p in project_list
    ), f"Unable to retrieve new project!\n{pformat(project_list)}"

    default_domino_client.project_archive(new_project_name)


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_project_fork(default_domino_client):
    """
    Confirm that the python-domino client can fork an existing project.
    """
    forked_project_name = f"forked-project-{str(uuid.uuid4())}"
    response = default_domino_client.fork_project(forked_project_name)
    assert response.status_code == 200, f"{response.status_code}: {response.reason}"

    project_list = default_domino_client.projects_list()
    assert any(
        p["name"] == forked_project_name for p in project_list
    ), f"Unable to retrieve forked project!\n{pformat(project_list)}"

    default_domino_client.project_archive(forked_project_name)


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_list_commits(default_domino_client):
    """
    Confirm that the python-domino client can list project commits.
    """
    commits_list = default_domino_client.commits_list()
    assert isinstance(
        commits_list, list
    ), f"Unable to retrieve commits:\n{pformat(commits_list)}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_list_files_in_commit(default_domino_client):
    """
    Confirm that the python-domino client can list the files of a given project commit.
    """
    commits_list = default_domino_client.commits_list()
    files_list = default_domino_client.files_list(commits_list[0])
    assert isinstance(
        files_list["data"], list
    ), f"Unable to retrieve files:\n{pformat(files_list)}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_upload_file_to_project(default_domino_client):
    """
    Confirm that the python-domino client can upload a file to a project.
    """
    with open(__file__, "rb") as test_file:
        response = default_domino_client.files_upload(
            path="/test_file.py", file=test_file
        )
    assert response.status_code == 201
    assert response.json()["path"] == "test_file.py"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_upload_file_to_project_without_forward_slash(default_domino_client):
    """
    Confirm that the python-domino client can upload a file to a project.
    """
    with open(__file__, "rb") as test_file:
        response = default_domino_client.files_upload(
            path="test_file.py", file=test_file
        )
    assert response.status_code == 201
    assert response.json()["path"] == "test_file.py"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_get_file_from_a_project(default_domino_client):
    """
    Confirm that the python-domino client can download a file from a project.
    """
    commits_list = default_domino_client.commits_list()
    files_list = default_domino_client.files_list(commits_list[0])

    for file in files_list["data"]:
        if file["path"] == ".dominoignore":
            file_contents = default_domino_client.blobs_get(file["key"]).read()
            break

    assert "ignore certain files" in str(
        file_contents
    ), f"Unable to get .dominoignore file\n{str(file_contents)}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_get_file_from_a_project_v2(default_domino_client):
    """
    Confirm that the python-domino client can download a file from a project in the v2 endpoint
    """
    commits_list = default_domino_client.commits_list()
    files_list = default_domino_client.files_list(commits_list[0])

    for file in files_list["data"]:
        if file["path"] == ".dominoignore":
            file_contents = default_domino_client.blobs_get_v2(file["path"], commits_list[0], default_domino_client.project_id).read()
            break

    assert "ignore certain files" in str(
        file_contents
    ), f"Unable to get .dominoignore file\n{str(file_contents)}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_get_blobs_v2_non_canonical(default_domino_client):
    """
    Confirm that the python-domino client get_blobs_v2 will fail if input path is non-canonical
    """
    non_canonical_path = "/domino/mnt/../test.py"
    commits_list = default_domino_client.commits_list()

    with pytest.raises(exceptions.MalformedInputException):
        default_domino_client.blobs_get_v2(non_canonical_path, commits_list[0], default_domino_client.project_id).read()


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_add_and_remove_project_collaborator(default_domino_client):
    """
    Confirm that the python-domino client can and/remove project collaborators.
    """

    def _get_users():
        url = default_domino_client._routes.users_get()
        response = default_domino_client.request_manager.get(url)
        assert response.status_code == 200, f"{response.status_code}: {response.reason}"
        return response.json()

    users_list = _get_users()
    collaborators = default_domino_client.collaborators_get()

    for user in users_list:
        username = user["userName"]
        if username not in collaborators:
            default_domino_client.collaborators_add(username)
            break

    new_collaborators = default_domino_client.collaborators_get()
    assert username in new_collaborators


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_publish_app_from_a_project(default_domino_client):
    """
    Confirm that the python-domino client can publish an app from a project.
    """
    response = default_domino_client.app_publish()
    assert response.status_code == 200, f"{response.status_code}: {response.reason}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_unpublish_app_from_a_project(default_domino_client):
    """
    Confirm that the python-domino client can unpublish an app from a project.
    """
    response = default_domino_client.app_unpublish()
    assert response.status_code == 200, f"{response.status_code}: {response.reason}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_tags_list_add_to_project(default_domino_client):
    """
    Confirm that the python-domino client can get and add tags a project.
    """
    first_tags = default_domino_client.tags_list()

    default_domino_client.tags_add(["new-tags"])
    new_tags = default_domino_client.tags_list()

    assert len(new_tags) > len(first_tags)

    assert any("new-tags" == tag["name"] for tag in new_tags)


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_tags_details(default_domino_client):
    """
    Confirm that the python-domino client can get tags details.
    """
    tag_name = "test-detail-tags"
    test_tag = default_domino_client.tags_add([tag_name])
    tag_id = test_tag.json()[0]["id"]
    detail_tag = default_domino_client.tag_details(tag_id)

    assert detail_tag["name"] == tag_name
    assert detail_tag["_id"] == tag_id
    assert detail_tag["lastAdded"] is not None

    default_domino_client.tags_remove(tag_name)


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_tags_list_remove_from_a_project(default_domino_client):
    """
    Confirm that the python-domino client can get and add tags a project.
    """
    first_tags = default_domino_client.tags_list()

    default_domino_client.tags_remove("new-tags")
    new_tags = default_domino_client.tags_list()

    assert len(new_tags) < len(first_tags)

    assert ("new-tags" != tag["id"] for tag in new_tags)
