import json

from .._client import client
from .._eval_tags import build_eval_result_tag, validate_label
from .._verify_domino_support import verify_domino_support
from .._constants import DOMINO_INTERNAL_EVAL_TAG


def add_domino_tags(trace_id: str):
    """
    Tags a trace as one that contains an evaluation
    Args:
        trace_id: string, the ID of the trace to tag
    """
    client.set_trace_tag(trace_id, DOMINO_INTERNAL_EVAL_TAG, json.dumps(True))


def log_evaluation(
        trace_id: str,
        name: str,
        value: float | str,
    ):
    """This logs evaluation data and metadata to a parent trace. This is used to log the evaluation of a span
    after it was created. This is useful for analyzing past performance of an AI System component.

    Args:
        trace_id: the ID of the trace to evaluate

        name: a label for the evaluation result. This is used to identify the evaluation result

        value: the evaluation result to log. This must be a float or string
    """
    verify_domino_support()
    validate_label(name)

    if value is not None:
        formatted_value = value
        if not isinstance(value, (str)):
            formatted_value = json.dumps(value)

        client.set_trace_tag(
            trace_id,
            build_eval_result_tag(name, value),
            formatted_value,
        )
        add_domino_tags(trace_id)


# TODO log feedback
