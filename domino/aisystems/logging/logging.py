import os
import mlflow
from typing import Optional, Callable, Any
import json
import time
import yaml
from datetime import datetime, timezone
from .._client import client

def add_domino_tags(
        span,
        is_prod: bool = False,
        extract_input_field: Optional[str] = None,
        extract_output_field: Optional[str] = None,
        is_eval: bool = False,
        sample: Optional[Any] = None,
    ):
    client.set_trace_tag(
        span.request_id,
        "domino.internal.is_production",
        json.dumps(is_prod)
    )
    client.set_trace_tag(
        span.request_id,
        "domino.internal.is_eval",
        json.dumps(is_eval)
    )

    raw_sample = sample or [span.inputs, span.outputs]

    # TODO I want to get rid of these
    if not sample and extract_input_field:
        raw_sample = [extract_subfield(span.inputs, extract_input_field), raw_sample[1]]

    if not sample and extract_output_field:
        raw_sample = [raw_sample[0], extract_subfield(span.outputs, extract_output_field)]

    if is_eval:
        tag_sample = None
        if sample:
            tag_sample = json.dumps(sample)
        else:
            tag_sample = '|'.join([json.dumps(s) for s in raw_sample])

        # TODO validate that sample is < 5 kb https://mlflow.org/docs/latest/api_reference/rest-api.html#request-structure
        client.set_trace_tag(
            span.request_id,
            f"domino.internal.{span.name}.sample",
            tag_sample
        )

def _is_production() -> bool:
    return os.getenv("DOMINO_EVALUATION_LOGGING_IS_PROD", "false") == "true"

def _get_prod_model_id() -> str:
    model_id = os.getenv("DOMINO_AI_SYSTEM_MODEL_ID", None)
    if not model_id:
        raise Exception("DOMINO_AI_SYSTEM_MODEL_ID environment variable must be set in production mode")

    return model_id

def _get_prod_logged_model():
    model_id = _get_prod_model_id()

    return mlflow.get_logged_model(model_id=model_id)

def log_evaluation(
        span,
        eval_result,
        eval_result_label: Optional[str] = None,
        sample: Optional[Any] = None,
        extract_input_field: Optional[str] = None,
        extract_output_field: Optional[str] = None,
    ):
    """This logs evaluation data and metdata to a parent trace. This is used to log the evaluation of a span
    after it was created. This is useful for analyzing past performance of an AI System component.

    Args:
        span: the span to evaluate

        eval_result: optional, the evaluation result to log. This must be a primitive type in order to enable
        more powerful data analysis

        eval_result_label: an optional label for the evaluation result. This is used to identify the evaluation result
        sample: An optional sample representing what was evaluated. It must be JSON serializable. The sample will default to the inputs and outputs of the span.
        extract_input_field: an optional dot separated string that specifies what subfield to access in the trace input
        extract_output_field: an optional dot separated string that specifies what subfield to access in the trace output
    """

    is_production = _is_production()
    # TODO can only do this if the span is status = 'OK' or 'ERROR'
    if eval_result:
        label = eval_result_label or "evaluation_result"

        client.set_trace_tag(
            span.request_id,
            f"domino.evaluation_result.{span.name}.{label}",
            json.dumps(eval_result),
        )
        client.set_trace_tag(
            span.request_id,
            f"domino.evaluation_label.{span.name}.{label}",
            "true"
        )
    add_domino_tags(span, is_production, extract_input_field, extract_output_field, is_eval=eval_result is not None, sample=sample)

# TODO name conflicts with Domino Runs and domino mlflow runs (Jobs)
# This just logs the AI System configuration
# TODO log the summary metric to the run
class DominoRun:
    def __init__(self, experiment_id=None, ai_system_config_path=None):
        self.experiment_id = experiment_id
        self.config_path = ai_system_config_path

    def __enter__(self):
        self._run = mlflow.start_run(experiment_id=self.experiment_id)
        if self.config_path:
            params = read_ai_system_config(self.config_path)
            params_flat = _flatten_dict(params)
            mlflow.log_params(params_flat)
        return self._run

    def __exit__(self, exc_type, exc_val, exc_tb):
        mlflow.end_run()

    def __call__(self):
        # same logic, but returns the run directly
        run = mlflow.start_run(experiment_id=self.experiment_id)
        if self.config_path:
            params = read_ai_system_config(self.config_path)
            params_flat = _flatten_dict(params)
            mlflow.log_params(params_flat)
        return run

# TODO log feedback
