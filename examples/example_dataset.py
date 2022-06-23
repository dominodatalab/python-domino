import os
from pprint import pprint
from domino import Domino

# requires
domino = Domino("integration-test/quick-start", host=os.environ["DOMINO_API_HOST"])

# raw_datasets = domino.datasets_list() #['data']
# print('Datasets:'+str(raw_datasets))

# Example using the current project's projectId to narrow down the datasets results to a specific project.
# Replace this value (5dbfc14b9f8d940006356eaa) below with a valid projectId that you have access to before running.
raw_created_datasets_for_project = domino.datasets_create(
    'My-New-Test-Dataset',
    'A dataset for testing purposes.'
)
print('Datasets for current project:'+str(raw_created_datasets_for_project))

# Get the details of a dataset, if one exists for the current project
raw_datasets_for_project = domino.datasets_list(domino.project_id)
dataset_id = raw_datasets_for_project[1]["datasetId"]
print("First returned dataset ID for current project: " + str(dataset_id))

# Update the details for the created dataset.
# git checkout -b DOM-38906-update-and-merge-datasets-endpoints
datasetId = str(dataset_id)
datasetName ="MyTestDataset"
datasetDescription = "An updated description for a dataset for testing purposes."

raw_datasets_update_details = domino.datasets_update_details(
    str(dataset_id),
    "MyTestDataset",
    "An updated description for a dataset for testing purposes.",
)

print(
    "Dataset with updated details for current project:"
    + str(raw_datasets_update_details)
)
