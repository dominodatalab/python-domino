import os


def get_is_production() -> bool:
    return os.environ.get("DOMINO_AGENT_IS_PROD", "false").lower() == "true"


def _get_agent_id() -> str | None:
    return os.environ.get("DOMINO_APP_ID")


def is_agent() -> bool:
    return get_is_production() and _get_agent_id() is not None


def build_agent_experiment_name(id: str) -> str:
    return f"agent_experiment_{id}"


def get_running_agent_experiment_name() -> str | None:
    if is_agent():
        return build_agent_experiment_name(_get_agent_id())
    return None
