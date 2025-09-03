import re

from ._constants import DOMINO_INTERNAL_EVAL_TAG, EVALUATION_TAG_PREFIX
from ..exceptions import DominoException

VALID_LABEL_PATTERN = r'[a-zA-Z0-9_-]+'

class InvalidEvaluationLabelException(DominoException):
    """Invalid evaluation label Exception"""

    pass

def validate_label(label: str):
    if not re.match(VALID_LABEL_PATTERN, label):
        raise InvalidEvaluationLabelException(f"label '{label}' may contain only alphanumeric characters, underscores and dashes.")

def build_metric_tag(metric_name: str) -> str:
    return f"{EVALUATION_TAG_PREFIX}.metric.{metric_name}"

def build_eval_result_tag(label: str, result) -> str:
    try:
        float(result)
        return build_metric_tag(label)
    except ValueError:
        # this result will be treated as a string
        # build label tag
        return f"{EVALUATION_TAG_PREFIX}.label.{label}"
