import os
import mlflow

def get_is_production() -> bool:
    return os.environ.get("DOMINO_AI_SYSTEM_IS_PROD", "false").lower() == "true"

def _get_ai_system_id() -> str | None:
    return os.environ.get("DOMINO_APP_ID")

def is_ai_system() -> bool:
    return get_is_production() and _get_ai_system_id() is not None

def build_ai_system_experiment_name(id: str) -> str:
    return id

def get_running_ai_system_experiment_name() -> str | None:
    if is_ai_system():
        return build_ai_system_experiment_name(_get_ai_system_id())
    return None
