import uuid
from pprint import pformat

import gzip
import pytest

from domino import Domino, exceptions
from domino.exceptions import ProjectNotFoundException
from domino.helpers import domino_is_reachable


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
        # This operation is not yet a public-facing part of the python-domino API
        url = default_domino_client._routes.users_get()
        response = default_domino_client.request_manager.get(url)
        assert response.status_code == 200, f"{response.status_code}: {response.reason}"
        return response.json()

    users_list = _get_users()
    collaborators = default_domino_client.collaborators_get()

    # Find a username that is not already a collaborator
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


def test_archiving_non_existent_project_raises_appropriate_error(
    dummy_hostname, requests_mock
):
    """
    Confirm that trying to archive a bogus project will throw the appropriate exception.
    """
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    projects_list_endpoint = "v4/gateway/projects?relationship=Owned&showCompleted=true"

    with pytest.raises(ProjectNotFoundException):
        requests_mock.get(
            f"{dummy_hostname}/{projects_list_endpoint}", json=[], status_code=200
        )
        d.project_archive("bogus_project")
