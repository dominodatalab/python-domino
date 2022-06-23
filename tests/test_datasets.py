import random

import pytest

from domino.helpers import domino_is_reachable


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
def test_datasets_remove(default_domino_client):
    datasets_ids = default_domino_client.datasets_ids(default_domino_client.project_id)
    default_domino_client.datasets_remove(datasets_ids[1:])

    new_datasets_ids = default_domino_client.datasets_ids(
        default_domino_client.project_id
    )

    assert datasets_ids[-1] not in new_datasets_ids
