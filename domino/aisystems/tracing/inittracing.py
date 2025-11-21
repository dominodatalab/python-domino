import logging
import mlflow
import threading
from typing import Optional

from .._client import client
from .._constants import EXPERIMENT_AI_SYSTEM_TAG
from ._util import is_ai_system, get_running_ai_system_experiment_name
from .._verify_domino_support import verify_domino_support

# init_tracing is not thread safe. this likely won't cause an issue with the autolog frameworks. If data inconsistency is caused with
# autolog frameworks, then the worst case scenario is that we get duplicate autolog calls. These are local to the process
# so not a big deal

global _triggered_autolog_frameworks
_triggered_autolog_frameworks = set()

global _is_prod_tracing_initialized
_is_prod_tracing_initialized = False

# Lock to ensure thread-safe access to _is_prod_tracing_initialized
global _prod_tracing_init_lock
_prod_tracing_init_lock = threading.Lock()


def init_tracing(autolog_frameworks: Optional[list[str]] = None):
    """Initialize Mlflow autologging for various frameworks and sets the active experiment to enable tracing in production.
    This may be used to initialize logging and tracing for the AI System in dev and prod modes.

    In prod mode, environment variables DOMINO_AI_SYSTEM_IS_PROD, DOMINO_APP_ID
    must be set. Call init_tracing before your app starts up to start logging traces to Domino.

    Args:
        autolog_frameworks: list of frameworks to autolog
    """
    verify_domino_support()
    frameworks = autolog_frameworks or []
    global _is_prod_tracing_initialized
    # Guard and initialization are protected by a lock for thread safety
    if is_ai_system():
        with _prod_tracing_init_lock:
            if not _is_prod_tracing_initialized:
                # activate ai system experiment
                logger.debug("Initializing mlflow tracing for AI System")

                # we use the client to create experiment and get to avoid racy behavior
                experiment = client.get_experiment_by_name(
                    get_running_ai_system_experiment_name()
                )
                if experiment is None:
                    experiment_name = get_running_ai_system_experiment_name()

                    logger.debug(
                        "Creating new experiment for AI System named %s",
                        experiment_name,
                    )

                    experiment_id = client.create_experiment(experiment_name)

                    logger.debug(
                        "Created experiment for AI System with ID %s", experiment_id
                    )

                    client.set_experiment_tag(
                        experiment_id, EXPERIMENT_AI_SYSTEM_TAG, "true"
                    )

                    logger.debug(
                        "Tagged experiment with ID %s with tag %s",
                        experiment_id,
                        EXPERIMENT_AI_SYSTEM_TAG,
                    )
                else:
                    experiment_id = experiment.experiment_id

                # only set experiment by ID to avoid the python client creating a new experiment with a random ID appended
                # this happens when init_tracing called by itself and then a domino trace started right after

                logger.debug(
                    "Setting AI System experiment with ID %s as active", experiment_id
                )

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
        logger.warning(f"Failed to call mlflow autolog for {fw} ai framework", e)


logger = logging.getLogger(__name__)
