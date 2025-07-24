import logging
import mlflow
import os
import re
import semver
from typing import Optional
from urllib.parse import urljoin
import yaml

from ..authentication import get_auth_by_type
from ._client import client
from ._constants import (MLFLOW_VERSION, MIN_DOMINO_VERSION, LARGEST_MAX_RESULTS_PAGE_SIZE, DOMINO_INTERNAL_EVAL_TAG,
    EVALUATION_TAG_PREFIX)
from ..exceptions import UnsupportedOperationException, InvalidEvaluationLabelException
from ..http_request_manager import _HttpRequestManager

VALID_LABEL_PATTERN = r'[a-zA-Z0-9_-]+'
DOMINO_EVAL_METRIC_TAG_PATTERN = f'domino.prog.metric.({VALID_LABEL_PATTERN})'

def _get_ai_system_config_path() -> str:
    return os.environ.get("DOMINO_AI_SYSTEM_CONFIG_PATH", "./ai_system_config.yaml")

def _get_version_endpoint() -> str:
    return urljoin(os.environ['DOMINO_API_HOST'], "version")

def _get_domino_version() -> str:
    req_manager = _HttpRequestManager(
        get_auth_by_type()
    )
    version_metadata = req_manager.get(_get_version_endpoint()).json()
    return version_metadata["version"]

def get_metric_tag_name(tag: str) -> Optional[str]:
    match = re.match(DOMINO_EVAL_METRIC_TAG_PATTERN, tag)
    if match:
        return match.group(1)
    return None

def is_metric_tag(tag: str) -> bool:
    return re.match(DOMINO_EVAL_METRIC_TAG_PATTERN, tag) is not None

def validate_label(label: str):
    if not re.match(VALID_LABEL_PATTERN, label):
        raise InvalidEvaluationLabelException(f"label '{label}' may contain only alphanumeric characters, underscores and dashes.")

def flatten_dict(d, parent_key='', sep='.'):
    """Recursively flattens a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def read_ai_system_config(path: Optional[str] = None) -> dict:
	path = path or _get_ai_system_config_path()
	params = {}
	try:
		with open(path, 'r') as f:
			params = yaml.safe_load(f)
	except Exception as e:
		logging.warning(f"Failed to read ai system config yaml at path {path}")
		logging.debug(e)

	return params

def get_is_production() -> bool:
    return os.environ.get("DOMINO_AI_SYSTEM_IS_PROD", "false").lower() == "true"

def build_metric_tag(metric_name: str) -> str:
    return f"{EVALUATION_TAG_PREFIX}.metric.{metric_name}"

def _build_label_tag(label_name: str) -> str:
    return f"{EVALUATION_TAG_PREFIX}.label.{label_name}"

def build_eval_result_tag(label: str, result) -> str:
    try:
        float(result)
        return build_metric_tag(label)
    except ValueError:
        # this result will be treated as a string
        return _build_label_tag(label)

def verify_domino_support():
    domino_supported = True
    try:
        # we do our best to get the Domino version. If this code runs in a Domino execution,
        # auth environment variables will be available. If they run this against a local mlflow server/not
        # Domino, it is ok if this check fails
        version = _get_domino_version()

        # verify Domino version is >= min domino version
        domino_supported = semver.Version.parse(version).compare(MIN_DOMINO_VERSION) > -1
    except Exception as e:
        # the user may run this outside of Domino, so we log a warning instead of failing
        logging.debug(f"Failed to get Domino version: {e}")

    if not domino_supported:
        raise UnsupportedOperationException("This version of Domino doesn’t support the aisystems package.")

    # verify mlflow sdk version
    mlflow_3_installed = semver.Version.parse(mlflow.__version__).compare(MLFLOW_VERSION) > -1

    if not mlflow_3_installed:
        raise UnsupportedOperationException(f"This code requires you to install mlflow>={MLFLOW_VERSION}")

def get_all_traces_for_run(experiment_id: str, run_id: str):
    filter_string = f"metadata.mlflow.sourceRun = '{run_id}' AND tags.{DOMINO_INTERNAL_EVAL_TAG} = 'true'"

    logging.debug(f"Searching for traces with filter: {filter_string}")

    next_page_token = None

    traces = client.search_traces(
        experiment_ids=[experiment_id],
        filter_string=filter_string,
        page_token=next_page_token,
        max_results=LARGEST_MAX_RESULTS_PAGE_SIZE,
        order_by=["attributes.timestamp_ms ASC"],
    )
    next_page_token = traces.token
    while next_page_token is not None:
        next_traces = client.search_traces(
            experiment_ids=[experiment_id],
            filter_string=filter_string,
            page_token=next_page_token,
            max_results=LARGEST_MAX_RESULTS_PAGE_SIZE,
            order_by=["attributes.timestamp_ms ASC"],
        )

        next_page_token = next_traces.token
        traces.extend(next_traces)

    return traces
