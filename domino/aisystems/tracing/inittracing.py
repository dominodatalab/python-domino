import logging
import mlflow
import os
from typing import Optional

from .._client import client
from .._constants import EXPERIMENT_AI_SYSTEM_TAG
from ._util import is_ai_system, get_running_ai_system_experiment_name
from .._verify_domino_support import verify_domino_support

# init_tracing is not thread safe. this likely won't cause an issue with the autolog frameworks. If data inconsistency is caused with
# autolog frameworks, then the worst case scenario is that we get duplicate autolog calls. These are local to the process
# so not a big deal
#
# TODO the experiment initialization needs further investigation in order to determine if we need
# to improve thread safety in order to reduce calls to the mlflow tracking server

global _triggered_autolog_frameworks
_triggered_autolog_frameworks = set()

global _is_prod_tracing_initialized
_is_prod_tracing_initialized = False

# should_reinitialize is for testing, in order to work around the _is_prod_tracing_initialized guard, so that
# we can have multiple tests for the init_tracing function
def init_tracing(autolog_frameworks: Optional[list[str]] = None, should_reinitialize: Optional[bool] = False):
    verify_domino_support()
    frameworks = autolog_frameworks or []
    """Initialize Mlflow autologging for various frameworks and set the active model for production evaluation runs.
    This may be used to initialize logging and tracing for the AI System in dev and prod modes.

    In prod mode, environment variables DOMINO_AI_SYSTEM_IS_PROD, DOMINO_APP_ID
    must be set. Call init_tracing before your app starts up to start logging traces to Domino.

    Args:
        autolog_frameworks: Optional[list[string]] of frameworks to autolog
    """
    global _is_prod_tracing_initialized
    if is_ai_system() and (not _is_prod_tracing_initialized or should_reinitialize):
        # activate ai system experiment
        logging.debug("Initializing mlflow tracing for AI System")

        # we use the client to create experiment and get to avoid racy behavior
        experiment = client.get_experiment_by_name(get_running_ai_system_experiment_name())
        if experiment is None:
            experiment_name = get_running_ai_system_experiment_name()

            logging.debug("Creating new experiment for AI System named %s", experiment_name)

            experiment_id = client.create_experiment(experiment_name)

            logging.debug("Created experiment for AI System with ID %s", experiment_id)

            client.set_experiment_tag(experiment_id, EXPERIMENT_AI_SYSTEM_TAG, "true")

            logging.debug("Tagged experiment with ID %s with tag %s", experiment_id, EXPERIMENT_AI_SYSTEM_TAG)
        else:
            experiment_id = experiment.experiment_id

        # only set experiment by ID to avoid the python client creating a new experiment with a random ID appended
        # this happens when init_tracing called by itself and then a domino trace started right after

        logging.debug("Setting AI System experiment with ID %s as active", experiment_id)

        experiment = mlflow.set_experiment(experiment_id=experiment_id)

        _is_prod_tracing_initialized = True

    for fw in frameworks:
        global _triggered_autolog_frameworks
        if fw not in _triggered_autolog_frameworks:
            _triggered_autolog_frameworks.add(fw)
            call_autolog(fw)

def call_autolog(fw: str):
    try:
        getattr(mlflow, fw).autolog()
    except Exception as e:
        logging.warning(f"Failed to call mlflow autolog for {fw} ai framework", e)
