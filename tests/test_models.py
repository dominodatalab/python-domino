from pprint import pformat

import pytest

from domino.helpers import domino_is_reachable


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
