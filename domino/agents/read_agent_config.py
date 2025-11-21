import logging
import os
from typing import Optional
import yaml


def _get_agent_config_path() -> str:
    return os.environ.get("DOMINO_AGENT_CONFIG_PATH", "./agent_config.yaml")


def flatten_dict(d, parent_key="", sep="."):
    """Recursively flattens a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_flattened_agent_config(path: Optional[str] = None) -> dict[str, any]:
    config = read_agent_config(path)
    return flatten_dict(config)


def read_agent_config(path: Optional[str] = None) -> dict:
    """For getting the agent_config.yaml file and reading it into a dictionary.
    If no path is provided it will look for the path in the DOMINO_AGENT_CONFIG_PATH. See environment variables
    docs for default values.

    Args:
        path: Location of the agent config yaml file.

    Returns:
        A dictionary of the agent config yaml values.

    """
    path = path or _get_agent_config_path()
    params = {}
    try:
            with open(path, 'r') as f:
                params = yaml.safe_load(f)
    except Exception as e:
            logging.warning(f"Failed to read agent config yaml at path {path}: {e}")

    return params


logger = logging.getLogger(__name__)
