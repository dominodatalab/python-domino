import logging
import mlflow
import os
from typing import Optional

from ._util import get_is_production
from .._util import verify_domino_support

global _active_prod_model_id
_active_prod_model_id = None

global _triggered_autolog_frameworks
_triggered_autolog_frameworks = set()

def _get_prod_model_id() -> str:
    model_id = os.getenv("DOMINO_AI_SYSTEM_MODEL_ID", None)
    if not model_id:
        raise Exception("DOMINO_AI_SYSTEM_MODEL_ID environment variable must be set in production mode")

    return model_id

def _get_prod_logged_model():
    model_id = _get_prod_model_id()
    return mlflow.get_logged_model(model_id=model_id)

def init_tracing(autolog_frameworks: Optional[list[str]] = None):
    verify_domino_support()
    frameworks = autolog_frameworks or []
    """Initialize Mlflow autologging for various frameworks and set the active model for production evaluation runs.
    This may be used to initialize logging and tracing for the AI System in dev and prod modes.
    If in prod mode, a DOMINO_AI_SYSTEM_MODEL_ID is required and represents the production AI System
    component. All traces will be linked to that model. No run is required.

    Args:
        autolog_frameworks: Optional[list[string]] of frameworks to autolog
    """
    # TODO when implemnenting prod tracing, must ensure AI System ID is set on trace metadata

    is_production = get_is_production()

    # NOTE: user provides the model name if they want to link traces to a
    # specific AI System. We will recommend this for production, but not for dev
    # evaluation
    global _active_prod_model_id
    if is_production and not _active_prod_model_id:
        model = _get_prod_logged_model()
        mlflow.set_active_model(model_id=model.model_id)

        _active_prod_model_id = model.model_id

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
