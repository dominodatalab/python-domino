import os
from pprint import pprint

from domino import Domino

# requires DOMINO_TOKEN_FILE environment variables, or api_token parameter
domino = Domino("integration-test/quick-start", host=os.environ["DOMINO_API_HOST"])

all_datasets = domino.datasets_list()
pprint(all_datasets)

# Example using the current project's projectId to narrow down the datasets results to a specific project.
project_datasets = domino.datasets_list(domino.project_id)
pprint(project_datasets)

# Get the details of a dataset
dataset_id = project_datasets[0]["datasetId"]
dataset_details = domino.datasets_details(dataset_id)
pprint(dataset_details)

#  Create dataset for current project
new_project_dataset = domino.datasets_create(
    "My-New-Test-Dataset-2", "A dataset for testing purposes."
)
pprint(new_project_dataset)

# Get the details of a dataset, if one exists for the current project
current_project_datasets = domino.datasets_list(domino.project_id)
dataset_id = current_project_datasets[1]["datasetId"]
pprint("First returned dataset ID for current project: " + dataset_id)

# Update the details for the created dataset.
new_dataset_name = "My-Test-Dataset-New-Name-2"
new_dataset_description = "An updated description for a dataset for testing purposes."

# Update the dataset name
datasets_name_update = domino.datasets_update_details(
    dataset_id=dataset_id, dataset_name=new_dataset_name
)
pprint(datasets_name_update)

# Update the dataset Description
datasets_description_update = domino.datasets_update_details(
    dataset_id=str(dataset_id),
    dataset_description="An updated description for a dataset for testing purposes.",
)

pprint(datasets_description_update)


# delete dataset
domino.datasets_remove([dataset_id])
pprint(domino.datasets_list(domino.project_id))
