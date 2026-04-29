"""
Tests for endpoint and model API methods.
In Domino, models are deployed as endpoints — these are tested together.
Unit tests at top (no live Domino deployment required).
Integration tests below (skipped unless a live deployment is reachable).
"""

from pprint import pformat

import pytest

from domino import Domino
from domino.helpers import domino_is_reachable

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_COMMIT_ID = "abc123def456"
MOCK_MODEL_ID = "aabbccddeeff001122334459"
MOCK_MODEL_VERSION_ID = "aabbccddeeff00112233445a"
MOCK_ENV_ID = "aabbccddeeff00112233445b"
MOCK_EXPORT_ID = "aabbccddeeff00112233445c"

MOCK_MODEL = {
    "id": MOCK_MODEL_ID,
    "name": "my-model",
    "projectId": MOCK_PROJECT_ID,
}

MOCK_MODEL_VERSION = {
    "id": MOCK_MODEL_VERSION_ID,
    "modelId": MOCK_MODEL_ID,
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
# API Endpoints (endpoint_state / endpoint_publish / endpoint_unpublish)
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_endpoint_state_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/anyuser/anyproject/endpoint/state",
        json={"status": "Running"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.endpoint_state()
    assert result["status"] == "Running"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_endpoint_unpublish_sends_delete(requests_mock, dummy_hostname):
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/v1/anyuser/anyproject/endpoint", status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.endpoint_unpublish()
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_endpoint_unpublish_returns_response(requests_mock, dummy_hostname):
    requests_mock.delete(
        f"{dummy_hostname}/v1/anyuser/anyproject/endpoint", status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    response = d.endpoint_unpublish()
    assert response.status_code == 200


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_endpoint_publish_sends_correct_payload(requests_mock, dummy_hostname):
    publish_mock = requests_mock.post(
        f"{dummy_hostname}/v1/anyuser/anyproject/endpoint/publishRelease",
        json={"status": "Published"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.endpoint_publish(file="predict.py", function="predict", commitId=MOCK_COMMIT_ID)
    body = publish_mock.last_request.json()
    assert body["commitId"] == MOCK_COMMIT_ID
    assert body["bindingDefinition"]["file"] == "predict.py"
    assert body["bindingDefinition"]["function"] == "predict"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_endpoint_publish_returns_response(requests_mock, dummy_hostname):
    requests_mock.post(
        f"{dummy_hostname}/v1/anyuser/anyproject/endpoint/publishRelease",
        json={"status": "Published"},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    response = d.endpoint_publish(
        file="predict.py", function="predict", commitId=MOCK_COMMIT_ID
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Model Endpoints (models_list / model_publish / model_version_*)
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_models_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/projects/anyuser/anyproject/models",
        json=[MOCK_MODEL],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.models_list()
    assert isinstance(result, list)
    assert result[0]["id"] == MOCK_MODEL_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_publish_sends_correct_payload(requests_mock, dummy_hostname):
    publish_mock = requests_mock.post(
        f"{dummy_hostname}/v1/models", json=MOCK_MODEL, status_code=200
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.model_publish(
        file="predict.py",
        function="predict",
        environment_id=MOCK_ENV_ID,
        name="my-model",
        description="test model",
    )
    body = publish_mock.last_request.json()
    assert body["name"] == "my-model"
    assert body["file"] == "predict.py"
    assert body["function"] == "predict"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_versions_get_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v1/models/{MOCK_MODEL_ID}/versions",
        json=[MOCK_MODEL_VERSION],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.model_versions_get(MOCK_MODEL_ID)
    assert isinstance(result, list)
    assert result[0]["id"] == MOCK_MODEL_VERSION_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_version_publish_sends_correct_payload(requests_mock, dummy_hostname):
    publish_mock = requests_mock.post(
        f"{dummy_hostname}/v1/models/{MOCK_MODEL_ID}/versions",
        json=MOCK_MODEL_VERSION,
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.model_version_publish(
        model_id=MOCK_MODEL_ID,
        file="predict.py",
        function="predict",
        environment_id=MOCK_ENV_ID,
        description="v2 of the model",
    )
    body = publish_mock.last_request.json()
    assert body["file"] == "predict.py"
    assert body["function"] == "predict"
    assert body["description"] == "v2 of the model"
    assert body["projectId"] == MOCK_PROJECT_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_version_export_sends_correct_payload(requests_mock, dummy_hostname):
    export_mock = requests_mock.post(
        f"{dummy_hostname}/v4/models/{MOCK_MODEL_ID}/{MOCK_MODEL_VERSION_ID}/exportImageToRegistry",
        json={"exportId": MOCK_EXPORT_ID},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.model_version_export(
        model_id=MOCK_MODEL_ID,
        model_version_id=MOCK_MODEL_VERSION_ID,
        registry_host="registry.example.com",
        registry_username="user",
        registry_password="pass",
        repository_name="my-repo",
        image_tag="latest",
    )
    body = export_mock.last_request.json()
    assert export_mock.called
    assert body["registryUrl"] == "registry.example.com"
    assert body["repository"] == "my-repo"
    assert body["tag"] == "latest"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_version_sagemaker_export_sends_post(requests_mock, dummy_hostname):
    export_mock = requests_mock.post(
        f"{dummy_hostname}/v4/models/{MOCK_MODEL_ID}/{MOCK_MODEL_VERSION_ID}/exportImageForSagemaker",
        json={"exportId": MOCK_EXPORT_ID},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.model_version_sagemaker_export(
        model_id=MOCK_MODEL_ID,
        model_version_id=MOCK_MODEL_VERSION_ID,
        registry_host="registry.example.com",
        registry_username="user",
        registry_password="pass",
        repository_name="my-repo",
        image_tag="latest",
    )
    body = export_mock.last_request.json()
    assert export_mock.called
    assert body["registryUrl"] == "registry.example.com"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_version_export_status_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/models/{MOCK_EXPORT_ID}/getExportImageStatus",
        json={"status": "Completed"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.model_version_export_status(MOCK_EXPORT_ID)
    assert result["status"] == "Completed"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_model_version_export_logs_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/models/{MOCK_EXPORT_ID}/getExportLogs",
        json={"logs": "export log output"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.model_version_export_logs(MOCK_EXPORT_ID)
    assert result["logs"] == "export log output"


# ---------------------------------------------------------------------------
# Integration tests (require a live Domino deployment)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_list_models(default_domino_client):
    """
    Confirm that the python-domino client can list the models from a project.
    """
    models_list = default_domino_client.models_list()
    assert (
        models_list["objectType"] == "list"
    ), f"models_list returned unexpected result:\n{pformat(models_list)}"
    assert isinstance(
        models_list["data"], list
    ), f"Unable to retrieve models:\n{pformat(models_list)}"


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_publish_a_model(default_domino_client):
    """
    Confirm that the python-domino client can publish a model.
    """
    filename = "model.py"
    function = "my_model"
    env_id = ""
    model_name = "Model Name"
    model_description = "Model Description"

    model = default_domino_client.model_publish(
        filename, function, env_id, model_name, model_description
    )

    assert model["data"]["name"] == model_name
    assert model["data"]["description"] == model_description


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_publish_model_version(default_domino_client):
    """
    Confirm that the python-domino client can publish a model version.
    """
    filename = "model.py"
    function = "my_model"
    env_id = ""
    model_name = "Model Name"
    model_description = "Model Description"

    model = default_domino_client.model_publish(
        filename, function, env_id, model_name, model_description
    )

    model_id = model["data"]["_id"]

    new_version = default_domino_client.model_version_publish(
        model_id, filename, function, env_id, model_name, model_description
    )
    assert new_version["number"] == 2
