import logging as logger
import os
import polling2
import pytest
import shutil
from unittest.mock import patch

from ...conftest import TEST_AI_SYSTEMS_ENV_VARS
from domino.aisystems._constants import MIN_MLFLOW_VERSION

@pytest.fixture
def tracing():
        pytest.importorskip("mlflow")
        import domino.aisystems.tracing as tracing
        yield tracing

@pytest.fixture
def logging():
        pytest.importorskip("mlflow")
        import domino.aisystems.logging as logging
        yield logging

@pytest.fixture
def mlflow():
        pytest.importorskip("mlflow")
        import mlflow
        yield mlflow

def _remove_mlruns_data():
        try:
                shutil.rmtree('./mlruns')
        except Exception as e:
                logger.warning(f"Failed to remove mlfruns directory during test cleanup: {e}")

@pytest.fixture(scope="package")
def setup_mlflow_tracking_server(docker_client):
        pytest.importorskip("mlflow")
        from mlflow import MlflowClient

        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS, clear=True):

                container_name = "test_mlflow_tracking_server"
                docker_client.containers.run(
                        f"ghcr.io/mlflow/mlflow:v{MIN_MLFLOW_VERSION}",
                        detach=True,
                        name=container_name,
                        ports={5000:5000},
                        command="mlflow ui --host 0.0.0.0",
                )

                try:
                        live_container = polling2.poll(
                                target=lambda: docker_client.containers.get(container_name),
                                check_success=lambda container: container.status == 'running',
                                timeout=10,
                                step=2,
                                ignore_exceptions=True,
                        )

                        # verify api is reachable
                        client = MlflowClient()
                        experiments = polling2.poll(
                                target=lambda: client.search_experiments(),
                                check_success=lambda exp: True,
                                timeout=10,
                                step=2,
                                ignore_exceptions=True,
                        )

                        yield live_container
                        live_container.remove(force=True)
                        _remove_mlruns_data()
                except Exception as e:
                        live_container = docker_client.containers.get(container_name)
                        container_status = live_container.status
                        logger.error(f'Mlflow tracking server did not get to running state. status: {container_status}')
                        logger.info(live_container.logs())
                        live_container.remove(force=True)
                        _remove_mlruns_data()
                        raise e
