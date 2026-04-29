"""
Tests for datasets API methods.
Unit tests at top (no live Domino deployment required).
Integration tests below (skipped unless a live deployment is reachable).
"""

import os
import random
from unittest.mock import patch

import pytest

from domino import Domino, exceptions
from domino.helpers import domino_is_reachable

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_DATASET_ID_1 = "bbccddeeff001122334455aa"
MOCK_DATASET_ID_2 = "ccddeeff001122334455aabb"

MOCK_DATASET_1 = {
    "datasetId": MOCK_DATASET_ID_1,
    "datasetName": "dataset-one",
    "datasetDescription": "First dataset",
    "projectId": MOCK_PROJECT_ID,
}
MOCK_DATASET_2 = {
    "datasetId": MOCK_DATASET_ID_2,
    "datasetName": "dataset-two",
    "datasetDescription": "Second dataset",
    "projectId": MOCK_PROJECT_ID,
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
def test_datasets_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1, MOCK_DATASET_2],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_list(MOCK_PROJECT_ID)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["datasetName"] == "dataset-one"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_list_without_project_id(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/dataset", json=[MOCK_DATASET_1])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_list()
    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_ids_returns_id_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1, MOCK_DATASET_2],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_ids(MOCK_PROJECT_ID)
    assert result == [MOCK_DATASET_ID_1, MOCK_DATASET_ID_2]


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_names_returns_name_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1, MOCK_DATASET_2],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_names(MOCK_PROJECT_ID)
    assert result == ["dataset-one", "dataset-two"]


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_details_returns_dataset(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset/{MOCK_DATASET_ID_1}", json=MOCK_DATASET_1
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_details(MOCK_DATASET_ID_1)
    assert result["datasetId"] == MOCK_DATASET_ID_1
    assert result["datasetName"] == "dataset-one"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_create_returns_new_dataset(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}", json=[])
    requests_mock.post(f"{dummy_hostname}/dataset", json=MOCK_DATASET_1)
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_create("dataset-one", "First dataset")
    assert result["datasetName"] == "dataset-one"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_create_raises_when_name_already_exists(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.DatasetExistsException):
        d.datasets_create("dataset-one", "Duplicate")


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_create_sends_correct_payload(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}", json=[])
    requests_mock.post(f"{dummy_hostname}/dataset", json=MOCK_DATASET_1)
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.datasets_create("dataset-one", "First dataset")
    body = requests_mock.last_request.json()
    assert body["datasetName"] == "dataset-one"
    assert body["description"] == "First dataset"
    assert body["projectId"] == MOCK_PROJECT_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_update_details_returns_updated_dataset(requests_mock, dummy_hostname):
    updated = {**MOCK_DATASET_1, "datasetDescription": "Updated description"}
    requests_mock.patch(f"{dummy_hostname}/dataset/{MOCK_DATASET_ID_1}", json={})
    requests_mock.get(f"{dummy_hostname}/dataset/{MOCK_DATASET_ID_1}", json=updated)
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.datasets_update_details(
        MOCK_DATASET_ID_1, dataset_description="Updated description"
    )
    assert result["datasetDescription"] == "Updated description"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_update_details_raises_when_new_name_already_exists(
    requests_mock, dummy_hostname
):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1, MOCK_DATASET_2],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.DatasetExistsException):
        d.datasets_update_details(MOCK_DATASET_ID_1, dataset_name="dataset-two")


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_dataset_remove_raises_when_dataset_missing(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}", json=[])
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.DatasetNotFoundException):
        d._dataset_remove("nonexistent-id")


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_dataset_remove_succeeds_when_dataset_exists(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1],
    )
    requests_mock.delete(
        f"{dummy_hostname}/dataset/{MOCK_DATASET_ID_1}", status_code=204
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    response = d._dataset_remove(MOCK_DATASET_ID_1)
    assert response.status_code == 204


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_remove_delegates_to_dataset_remove(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1, MOCK_DATASET_2],
    )
    requests_mock.delete(
        f"{dummy_hostname}/dataset/{MOCK_DATASET_ID_1}", status_code=204
    )
    requests_mock.delete(
        f"{dummy_hostname}/dataset/{MOCK_DATASET_ID_2}", status_code=204
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    responses = d.datasets_remove([MOCK_DATASET_ID_1, MOCK_DATASET_ID_2])
    assert len(responses) == 2
    assert all(r.status_code == 204 for r in responses)


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_datasets_remove_raises_for_missing_id(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/dataset?projectId={MOCK_PROJECT_ID}",
        json=[MOCK_DATASET_1],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    with pytest.raises(exceptions.DatasetNotFoundException):
        d.datasets_remove([MOCK_DATASET_ID_2])


# ---------------------------------------------------------------------------
# Integration tests (require a live Domino deployment)
# ---------------------------------------------------------------------------


@pytest.fixture
def random_seq():
    rand_val = random.randint(1000, 8888)
    rand_val2 = random.randint(1000, 8888)
    return f"-{rand_val}-{rand_val2}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_create_and_ids(default_domino_client, random_seq):
    dataset_name = "My-Integration-Test-Dataset" + random_seq
    dataset_desc = "A dataset for testing purposes."
    new_dataset = default_domino_client.datasets_create(
        dataset_name=dataset_name, dataset_description=dataset_desc
    )

    datasets_ids = default_domino_client.datasets_ids(default_domino_client.project_id)

    assert dataset_name == new_dataset["datasetName"]
    assert dataset_desc == new_dataset["description"]
    assert new_dataset["datasetId"] in datasets_ids


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_list(default_domino_client):
    datasets = default_domino_client.datasets_list()
    project_datasets = default_domino_client.datasets_list(
        default_domino_client.project_id
    )
    dataset_id = project_datasets[0]["datasetId"]

    assert datasets is not None
    assert project_datasets is not None
    assert dataset_id is not None


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_update_details_and_name(default_domino_client, random_seq):
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        1
    ]

    new_datasets_name = "My-New-Integration-Test-Dataset" + random_seq
    new_datasets_description = "My New Integration Test Dataset Description"

    new_dataset = default_domino_client.datasets_update_details(
        datasets_id, dataset_name=new_datasets_name
    )
    newer_dataset = default_domino_client.datasets_update_details(
        datasets_id, dataset_description=new_datasets_description
    )

    datasets_names = default_domino_client.datasets_names(
        default_domino_client.project_id
    )

    assert new_datasets_name == new_dataset["datasetName"]
    assert new_datasets_name in datasets_names
    assert new_datasets_description == newer_dataset["description"]


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_details(default_domino_client, random_seq):
    new_dataset_name = "My-New-Integration-Test-Dataset-3" + random_seq
    new_dataset_description = "My New Integration Test Dataset Description 4"

    new_dataset = default_domino_client.datasets_create(
        dataset_name=new_dataset_name, dataset_description=new_dataset_description
    )

    new_dataset_id = new_dataset["datasetId"]

    dataset_details = default_domino_client.datasets_details(new_dataset_id)

    assert dataset_details is not None
    assert new_dataset_name == new_dataset["datasetName"]
    assert new_dataset_description == new_dataset["description"]
    assert "projectId" in dataset_details.keys()
    assert "created" in dataset_details.keys()


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_upload(default_domino_client):
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        0
    ]
    assert "test_datasets.py" in os.listdir("tests")
    local_path_to_file = "tests/test_datasets.py"
    response = default_domino_client.datasets_upload_files(
        datasets_id, local_path_to_file
    )

    assert "test_datasets.py" in response


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_upload_with_sub_dir(default_domino_client):
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        0
    ]
    assert "test_datasets.py" in os.listdir("tests")
    local_path_to_file = "tests/test_datasets.py"
    response = default_domino_client.datasets_upload_files(
        datasets_id, local_path_to_file, target_relative_path="sub_d"
    )
    assert "test_datasets.py" in response


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@patch("os.path.exists")
def test_datasets_upload_mixed_slash_path(mock_exists, default_domino_client):
    mock_exists.return_value = True
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        0
    ]
    assert "back\\slash.txt" in os.listdir("tests/assets")
    local_path_to_file = "tests/assets/back\\slash.txt"
    response = default_domino_client.datasets_upload_files(
        datasets_id, local_path_to_file
    )
    assert "back\\slash.txt" in response


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@patch("os.path.exists")
def test_datasets_upload_windows_path(mock_exists, default_domino_client):
    mock_exists.return_value = True
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        0
    ]
    assert "test_datasets.py" in os.listdir("tests")
    windows_local_path_to_file = "tests\\test_datasets.py"
    response = default_domino_client.datasets_upload_files(
        datasets_id, windows_local_path_to_file
    )
    assert "test_datasets.py" in response


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@patch("os.path.exists")
def test_datasets_upload_with_sub_dir_windows_path(mock_exists, default_domino_client):
    mock_exists.return_value = True
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        0
    ]
    assert "test_datasets.py" in os.listdir("tests")
    windows_local_path_to_file = "tests\\test_datasets.py"
    response = default_domino_client.datasets_upload_files(
        datasets_id, windows_local_path_to_file, target_relative_path="sub_d"
    )

    assert "test_datasets.py" in response


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@patch("os.path.exists")
def test_datasets_upload_directory_windows_path(mock_exists, default_domino_client):
    mock_exists.return_value = True
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        0
    ]
    assert os.path.isdir("tests/assets")
    windows_local_path_to_dir = "tests/assets"
    response = default_domino_client.datasets_upload_files(
        datasets_id, windows_local_path_to_dir
    )
    assert "tests/assets" in response


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_upload_non_existing_file(default_domino_client):
    datasets_id = default_domino_client.datasets_ids(default_domino_client.project_id)[
        1
    ]
    local_path_to_file = "non_existing_file.py"
    try:
        default_domino_client.datasets_upload_files(datasets_id, local_path_to_file)
        assert False
    except ValueError:
        assert True


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_datasets_remove(default_domino_client):
    datasets_ids = default_domino_client.datasets_ids(default_domino_client.project_id)
    default_domino_client.datasets_remove(datasets_ids[1:])

    new_datasets_ids = default_domino_client.datasets_ids(
        default_domino_client.project_id
    )

    assert datasets_ids[-1] not in new_datasets_ids
