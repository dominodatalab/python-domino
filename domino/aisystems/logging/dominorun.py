import itertools
import logging
import mlflow
import re
from statistics import median, stdev
import traceback
from typing import Literal, Optional, Callable

from .._client import client
from .._constants import LARGEST_MAX_RESULTS_PAGE_SIZE, DOMINO_INTERNAL_EVAL_TAG
from .._util import build_metric_tag, VALID_LABEL_PATTERN
from .._verify_domino_support import verify_domino_support
from ..read_ai_system_config import get_flattened_ai_system_config

TOTAL_DECIMAL_PLACES = 3
DOMINO_EVAL_METRIC_TAG_PATTERN = f'domino.prog.metric.({VALID_LABEL_PATTERN})'

SummaryStatistic = Literal["mean", "median", "stdev", "max", "min"]

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

def is_metric_tag(tag: str) -> bool:
    return re.match(DOMINO_EVAL_METRIC_TAG_PATTERN, tag) is not None

def get_metric_tag_name(tag: str) -> Optional[str]:
    match = re.match(DOMINO_EVAL_METRIC_TAG_PATTERN, tag)
    if match:
        return match.group(1)
    return None

def _parse_value(v):
    try:
        return float(v)
    except ValueError as e:
        logging.warning(f"Failed to parse value {v} as float: {e}")
        raise e

def _get_experiment_id_from_name(name: Optional[str]):
    if name:
        exp = mlflow.get_experiment_by_name(name)
        if not exp:
            raise Exception(f"Could not find experiment with name {name}")
        return exp.experiment_id
    return None

def _choose_summarizer(statistic: SummaryStatistic) -> Callable[[list[float]], float]:
    match statistic:
        case "mean":
            return lambda values: round(sum(values) / len(values), TOTAL_DECIMAL_PLACES)
        case "median":
            return lambda values: median(sorted(values))
        case "stdev":
            return lambda values: round(stdev(values), TOTAL_DECIMAL_PLACES)
        case "max":
            return max
        case "min":
            return min
        case _:
            raise ValueError(f"Unknown summary statistic: {statistic}")

"""
DominoRun is a context manager that starts an Mlflow run and attaches the user's AI System configuration to it,
create a Logged Model with the AI System configuration, and computes summary metrics for evaluation traces made during the run.
Average metrics are computed by default, but the user can provide a custom list of evaluation metric aggregators.
This is intended to be used in development mode for AI System evaluation.
Context manager docs: https://docs.python.org/3/library/contextlib.html

Example:
    import mlflow

    mlflow.set_experiment("my_experiment")

    with DominoRun():
        train_model()
"""
class DominoRun:
    def __init__(self,
        experiment_name: Optional[str] = None,
        run_id: Optional[str] = None,
        ai_system_config_path: Optional[str] = None,
        custom_summary_metrics: Optional[list[(str, SummaryStatistic)]] = None
    ):
        """
        Args:
                experiment_name: the name of the mlflow experiment to log the run to.

                run_id: optional, the ID of the mlflow run to continue logging to. If not provided a new run will start.

                ai_system_config_path: the optional path to the AI System configuraiton file. If not provided, defaults to the
                        DOMINO_AI_SYSTEM_CONFIG_PATH environment variable.

                custom_summary_metrics: an optional list of tuples that define what summary statistic to use with what evaluation metric.
                Valid summary statistics are: "mean", "median", "stddev", "max", "min" e.g. [("hallucination_rate", "max")]

        Returns: DominoRun context manager
        """
        verify_domino_support()
        self.experiment_name = experiment_name
        self.run_id = run_id
        self.config_path = ai_system_config_path
        self.custom_summary_metrics = custom_summary_metrics
        self.experiment_id = _get_experiment_id_from_name(experiment_name)
        self._run = None

        self._validate()

    def _validate(self):
        # validate custome summary metrics
        if self.custom_summary_metrics:
            for (_, stat) in self.custom_summary_metrics:
                _choose_summarizer(stat)

    def _start_run(self):
        """
        Starts an mlflow run, either by continueing an existing run or starting a new one,
        and saves the experiment ID of the run in order to support starting runs
        without a user specifying the experiment explicitly.
        """
        if not self._run:
            if self.experiment_id:
                self._run = mlflow.start_run(experiment_id=self.experiment_id, run_id=self.run_id)
            elif self.run_id:
                self._run = mlflow.get_run(run_id=self.run_id)
            else:
                self._run = mlflow.start_run()

            self.experiment_id = self._run.info.experiment_id

    def __enter__(self):
        """
        Called when the 'with' block is executed
        """
        self._start_run()
        self.__log_params(self._run.info.run_id)

        return self._run

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when the 'with' block ends
        """
        try:
            traces = get_all_traces_for_run(self.experiment_id, self._run.info.run_id)

            # group by evaluation name
            eval_tags = sorted([(key, value) for t in traces for (key, value) in t.info.tags.items() if is_metric_tag(key)], key=lambda x: x[0])
            grouped_eval_tags = dict([(k, list(vs)) for (k, vs) in itertools.groupby(eval_tags, key=lambda x: x[0])])

            summary_metric_specs = self.custom_summary_metrics or [(get_metric_tag_name(tag), "mean") for tag, _ in grouped_eval_tags.items()]
            for (eval_label, summary_statistic) in summary_metric_specs:
                aggregator = _choose_summarizer(summary_statistic)
                tag = build_metric_tag(eval_label)
                found_values = grouped_eval_tags.get(tag, None)
                if found_values:
                    try:
                        values = [_parse_value(v) for (_, v) in found_values]
                        summary = aggregator(values)
                        mlflow.log_metric(tag, summary, run_id=self._run.info.run_id)
                    except Exception as e:
                        logging.error(f"Failed to log summarization metric for {tag}: {e}")
                else:
                    logging.debug(f"No evaluation tags found for {tag}, skipping summarization metric logging")
        except Exception as e:
            logging.error(
                f"Something went wrong while computing summarization metric for run {self._run.info.run_id}: {e}"
            )
            traceback.print_exc()

        mlflow.end_run()

    def __log_params(self, run_id: str):
        """
        Saves the user's AI System configuration as parameters to the mlflow run and
        the AI System's logged model
        """
        try:
            params = get_flattened_ai_system_config(self.config_path)
            mlflow.log_params(params, run_id=run_id)

            mlflow.create_external_model(
                model_type="AI System",
                params=params,
                source_run_id=run_id,
            )
        except Exception as e:
            logging.error(f"Failed to log AI System configuration to run {run_id}: {e}")
