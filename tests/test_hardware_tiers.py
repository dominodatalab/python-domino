import uuid
from pprint import pformat

import pytest

from domino import Domino
from domino.helpers import domino_is_reachable
from domino.exceptions import ProjectNotFoundException


@pytest.mark.skipif(not domino_is_reachable(), reason="No access to a live Domino deployment")
def test_hardware_tier_create(default_domino_client):
    """
    Confirm that the python-domino client can create a new project.
    """
    new_project_name = f"project-{str(uuid.uuid4())}"
    response = default_domino_client.project_create(new_project_name)
    assert response.status_code == 200, f"{response.status_code}: {response.reason}"

    project_list = default_domino_client.projects_list()
    assert any(p['name'] == new_project_name for p in project_list), \
        f"Unable to retrieve new project!\n{pformat(project_list)}"

    default_domino_client.project_archive(new_project_name)

@pytest.mark.skipif(not domino_is_reachable(), reason="No access to a live Domino deployment")
def test_archiving_non_existent_hardware_tier_raises_appropriate_error(dummy_hostname, requests_mock):
    """
    Confirm that trying to archive a bogus hardware tier will throw the appropriate exception.
    """
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")

    projects_list_endpoint = "v4/gateway/projects?relationship=Owned&showCompleted=true"

    with pytest.raises(ProjectNotFoundException):
        requests_mock.get(f"{dummy_hostname}/{projects_list_endpoint}", json=[], status_code=200)
        d.project_archive("bogus_project")