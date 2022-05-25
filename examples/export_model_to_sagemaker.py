# Required for AWS ECR registry credentials access
import boto3
from base64 import b64decode

# Required for Domino APIs
from domino import Domino

# Additional libraries for this example
import os
from time import sleep
import pprint

# Set this to your AWS ECR repository name
AWS_ECR_REPOSITORY_NAME = "domino-model-exports"

# How often, in seconds, to check the status of the model export
SLEEP_TIME_SECONDS = 10


# First, obtain the ECR registry details from AWS
# Be sure to have the environment variables AWS_ACCESS_KEY_ID,
#  AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION set for the boto3 library to
#  work. Otherwise, please see the boto3 documentation on how to use AWS tokens
#  with the library. The AWS credentials need to have write access to the
#  repository name you defined above.
aws_account = boto3.client("sts").get_caller_identity().get("Account")
aws_ecr_auth = boto3.client("ecr").get_authorization_token(registryIds=[aws_account])
aws_ecr_registry = (
    aws_ecr_auth["authorizationData"][0]["proxyEndpoint"]
    .lstrip("https://")
    .lstrip("http://")
)
aws_ecr_credentials = (
    b64decode(aws_ecr_auth["authorizationData"][0]["authorizationToken"])
    .decode("utf-8")
    .split(":")
)
aws_ecr_username = aws_ecr_credentials[0]
aws_ecr_password = aws_ecr_credentials[1]

# Connect to domino; be sure to have the DOMINO_API_HOST,
#  DOMINO_PROJECT_OWNER, DOMINO_PROJECT_NAME, and DOMINO_USER_API_KEY
#  environment variables set
#  (runs inside a Domino executor automatically set these for you)
domino = Domino(
    project="{0}/{1}".format(
        os.environ["DOMINO_PROJECT_OWNER"], os.environ["DOMINO_PROJECT_NAME"]
    ),
    api_key=os.environ["DOMINO_USER_API_KEY"],
    host=os.environ["DOMINO_API_HOST"],
)

# Grab a list of all models in the project
project_models = domino.models_list()

# We'll get the first model, assuming there is at least one model in the
#  project
model_id = project_models["data"][0]["id"]

# Get information about every model version for this model and desc sort these
#  by the model number
model_versions = sorted(
    domino.model_versions_get(model_id)["data"],
    key=lambda ver: ver["metadata"]["number"],
    reverse=True,
)

# Let's get the latest version of this model
model_version_id = model_versions[0]["_id"]

# Initiate export of model as SageMaker-compatible Docker image
#  Be sure
model_export_image_tag = "domino-{PROJECT_OWNER}-{PROJECT_NAME}-{MODEL_ID}-{MODEL_VERSION_ID}".format(
    PROJECT_OWNER=os.environ["DOMINO_PROJECT_OWNER"],
    PROJECT_NAME=os.environ["DOMINO_PROJECT_NAME"],
    MODEL_ID=model_id,
    MODEL_VERSION_ID=model_version_id,
)

print(
    "Exporting model {PROJECT_OWNER}/{PROJECT_NAME}/{MODEL_ID}/{MODEL_VERSION_ID} to AWS ECR repoistory {ECR_REGISTRY}/{ECR_REPOSITORY}:{IMAGE_TAG} as SageMaker-compatiable Docker image".format(
        PROJECT_OWNER=os.environ["DOMINO_PROJECT_OWNER"],
        PROJECT_NAME=os.environ["DOMINO_PROJECT_NAME"],
        MODEL_ID=model_id,
        MODEL_VERSION_ID=model_version_id,
        ECR_REGISTRY=aws_ecr_registry,
        ECR_REPOSITORY=AWS_ECR_REPOSITORY_NAME,
        IMAGE_TAG=model_export_image_tag,
    )
)

model_export = domino.model_version_sagemaker_export(
    model_id=model_id,
    model_version_id=model_version_id,
    registry_host=aws_ecr_registry,
    registry_username=aws_ecr_username,
    registry_password=aws_ecr_password,
    repository_name=AWS_ECR_REPOSITORY_NAME,
    image_tag=model_export_image_tag,
)

# Display the export status
model_export_status = model_export.get("status", None)
while model_export_status not in ["complete", "failed"]:
    if model_export_status:
        print(model_export_status)

    sleep(SLEEP_TIME_SECONDS)

    model_export = domino.model_version_export_status(model_export["exportId"])
    model_export_status = model_export.get("status", None)

# Lastly, print the logs of the Docker image build and export
model_export_logs = domino.model_version_export_logs(model_export["exportId"])
pprint.pprint(model_export_logs)
