from dataclasses import dataclass
from datetime import datetime, timedelta
import functools
import inspect
import logging
import mlflow
from typing import Optional, Callable, Any, TypeVar
from uuid import uuid4

from .._client import client
from .inittracing import init_tracing
from ..logging.logging import log_evaluation, add_domino_tags
from ._util import get_is_production, build_ai_system_experiment_name
from .._eval_tags import validate_label, get_eval_tag_name
from .._verify_domino_support import verify_domino_support

T = TypeVar('T')
Evaluator = Callable[[T, T], dict[str, int | float | str]]

@dataclass
class SpanSummary:
    id: str
    name: str
    trace_id: str
    inputs: Any
    outputs: Any

@dataclass
class TraceSummary:
    name: str
    id: str
    spans: list[SpanSummary]

@dataclass
class EvaluationResult:
    name: str
    value: float | str

@dataclass
class TraceSummary:
    name: str
    id: str
    spans: list[SpanSummary]
    evaluation_results: list[EvaluationResult]

@dataclass
class SearchTracesResponse:
    data: list[TraceSummary]
    page_token: str

def _datetime_to_ms(dt: datetime) -> int:
    return dt.timestamp() * 1000

def _make_span_summary(span: mlflow.entities.Span) -> SpanSummary:
    return SpanSummary(
        id=span.span_id,
        name=span.name,
        trace_id=span.trace_id,
        inputs=span.inputs,
        outputs=span.outputs,
    )

def _do_evaluation(
        span: mlflow.entities.Span,
        evaluator: Optional[Evaluator] = None,
        is_production: bool = False) -> Optional[dict]:

        if not is_production and evaluator:
            try:
                return evaluator(span.inputs, span.outputs)
            except Exception as e:
                logging.error(
                    "Inline evaluation failed for evaluator, %s. Error: %s" , evaluator.__name__, e, exc_info=True
                )

        return None

def _log_eval_results(parent_span: mlflow.entities.Span, evaluator: Optional[Evaluator]):
    """
    Saves the evaluation results
    """
    is_production = get_is_production()
    eval_result = _do_evaluation(parent_span, evaluator, is_production)

    if eval_result:
        for (k, v) in eval_result.items():
            # save the evaluation result for the trace
            log_evaluation(
                parent_span.request_id,
                value=v,
                name=k,
            )

def _set_span_inputs(parent_span, func, args, kwargs):
    """
    Sets the inputs on the span. Takes the arguments passed to the decorated function
    and preserves names of positional arguments, ensures defaults are applied, and excludes
    'self' and 'cls'  in the case of class methods and instance methods, because the user doesn't
    explicitly pass these in via the args and we want the arguments to match what the user expects
    """
    bound_args = inspect.signature(func).bind(*args, **kwargs)
    bound_args.apply_defaults()
    inputs = {k: v for k, v in bound_args.arguments.items() if k != 'self' and k != 'cls'}
    parent_span.set_inputs(inputs)

    return inputs

def add_tracing(
        name: str,
        autolog_frameworks: Optional[list[str]] = [],
        evaluator: Optional[Evaluator] = None,
        eagerly_evaluate_streamed_results: bool = True,
    ):
    """A decorator that starts an mlflow span for the function it decorates. If there is an existing trace
    this span will be appended to it.

    It also enables the user to run an evaluation inline in the code is run in development mode on
    the inputs and outputs of the wrapped function call.
    The user can provide input and output formatters for formatting what's on the trace
    and the evaluation result inputs, which can be used by client's to extract relevant data when
    analyzing a trace.

    This decorator must be used directly on the function to be traced, because it must have access to the
    arguments.

    @add_tracing(
        name="assistant_chat_bot",
        evaluator=evaluate_helpfulness,
    )
    def ask_chat_bot(user_input: str) -> dict:
        ...

    Args:
        name: the name of the span to add to existing trace or create if no trace exists yet.

        autolog_frameworks: an optional list of mlflow supported frameworks to autolog

        evaluator: an optional function that takes the inputs and outputs of the wrapped function and returns
        a dictionary of evaluation results. The evaluation result will be added to the trace as tags.

        eagerly_evaluate_streamed_results: optional boolean, defaults to true, this determines if all
            yielded values should be aggregated and set as outputs to a single span. This makes evaluation eaiser, but
            will impact performance if you expect a large number of streamed values. If set to false, each yielded value
            will generate a new span on the trace, which can be evaluated post-hoc. Inline evaluators won't be executed.
            Each span will have a group_id set in their attributes to indicate that they are part of the same function call.
            Each span will have an index to indicate what order they arrived in.

    Returns:
        A decorator that wraps the function to be traced.
    """
    validate_label(name)

    def decorator(func):

        # For Regular Functions (e.g., langgraph_agents.run_agent)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            init_tracing(autolog_frameworks)

            with mlflow.start_span(name) as parent_span:
                _set_span_inputs(parent_span, func, args, kwargs)

                result = func(*args, **kwargs)

                parent_span.set_outputs(result)

                _log_eval_results(parent_span, evaluator)

                return result

        # for async functions
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                init_tracing(autolog_frameworks)

                with mlflow.start_span(name) as parent_span:
                    _set_span_inputs(parent_span, func, args, kwargs)

                    result = await func(*args, **kwargs)

                    parent_span.set_outputs(result)

                    _log_eval_results(parent_span, evaluator)

                    return result

            return async_wrapper

        # For Generator Functions (e.g., RAGAgent.answer)
        if inspect.isgeneratorfunction(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                init_tracing(autolog_frameworks)

                with mlflow.start_span(name) as parent_span:
                    inputs = _set_span_inputs(parent_span, func, args, kwargs)

                    result = func(*args, **kwargs)

                    eval_result = None

                    if not eagerly_evaluate_streamed_results:
                        # can't do inline evaluation, so warn if an evaluator is provided
                        if evaluator:
                            logging.warning(
                                """eagerly_evaluate_streamed_results is false, so inline evaluation is disabled.
                                You can still do evaluations using log_evaluation post-hoc"""
                            )

                        group_id = uuid4()
                        i = -1
                        for v in result:
                            i += 1
                            with mlflow.start_span(name) as gen_span:
                                # make span for each yielded value
                                gen_span.set_inputs(inputs)
                                gen_span.set_attributes({"group_id": str(group_id), "index": i})
                                yield v
                                gen_span.set_outputs(v)
                    else:
                        # get all results and set as outputs
                        all_results = [v for v in result]
                        parent_span.set_outputs(all_results)
                        _log_eval_results(parent_span, evaluator)

                        for v in all_results:
                            yield v

            return wrapper


        return wrapper
    return decorator

def _build_evaluation_result(tag_key: str, tag_value: str) -> EvaluationResult:
    value = tag_value
    try:
        value = float(tag_value)
    except:
        pass

    return EvaluationResult(name=get_eval_tag_name(tag_key), value=value)

def _build_trace_summaries(traces) -> list[TraceSummary]:
    trace_summaries = []
    for trace in traces:
        # build trace summaries if there is a span location for the trace
        parent_span = trace.data.spans[0]
        trace_name = parent_span.name
        spans = trace.data.spans

        trace_summaries.append(
            TraceSummary(
                name=trace_name,
                id=trace.info.trace_id,
                spans=[_make_span_summary(s) for s in spans],
                evaluation_results=[_build_evaluation_result(key, value) for (key, value) in trace.info.tags.items() if get_eval_tag_name(key) is not None],
            )
        )

    return trace_summaries

def search_traces(
  run_id: Optional[str] = None,
  ai_system_id: Optional[str] = None,
  ai_system_version: Optional[str] = None,
  trace_name: Optional[str] = None,
  start_time: Optional[datetime] = None,
  end_time: Optional[datetime] = None,
  page_token: Optional[str] = None,
  max_results: Optional[int] = None,
) -> SearchTracesResponse:
    # this depends on mlflow 3 due to the pagination support
    verify_domino_support()
    """This allows searching for traces that have a certain name and returns a paginated response of trace summaries that
    inclued the spans that were requested.

    Args:
        run_id: string, the ID of the development mode evaluation run to search for traces.
        trace_name: the name of the traces to search for
        start_time: python datetime
        end_time: python datetime, defaults to now
        page_token: page token for pagination. You can use this to request the next page of results and may
         find a page_token in the response of the previous search_traces call.
        max_results: defaults to 100

    Returns:
        SearchTracesReponse: a token based pagination response that contains a list of trace summaries
            data: list of TraceSummary
            page_token: the next page's token
    """

    if not run_id and not ai_system_version and not ai_system_id:
        raise Exception("Either run_id or ai_system_id and ai_system_version must be provided to search traces")

    if ai_system_version and not ai_system_id:
        raise Exception("If ai_system_version is provided, ai_system_id must also be provided")

    # get experiment id
    if run_id:
        experiment_id = client.get_run(run_id).info.experiment_id
    else:
        experiment_name = build_ai_system_experiment_name(ai_system_id, ai_system_version)
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            raise Exception(f"No experiment found for ai_system_id: {ai_system_id} and ai_system_version: {ai_system_version}")
        experiment_id = experiment.experiment_id

    time_range_filter_clause = ''
    if start_time:
        start_ms = _datetime_to_ms(start_time)
        time_range_filter_clause += f'timestamp_ms > {start_ms}'

    if end_time:
        end_ms = _datetime_to_ms(end_time)
        time_range_filter_clause += f' AND timestamp_ms < {end_ms}'

    trace_name_filter_clause = None
    if trace_name:
        trace_name_filter_clause = f'trace.name = "{trace_name}"'

    # get traces made within the time range
    # get traces with the trace names
    run_filter_clause = f'metadata.mlflow.sourceRun = "{run_id}"'
    filter_clauses = [run_filter_clause, time_range_filter_clause, trace_name_filter_clause]
    filter_string = ' AND '.join([x for x in filter_clauses if x])

    traces = client.search_traces(
        experiment_ids=[experiment_id],
        filter_string=filter_string,
        page_token=page_token,
        max_results=max_results or 100,
        order_by=["attributes.timestamp_ms ASC"],
    )

    trace_summaries = _build_trace_summaries(traces)
    next_page_token = traces.token

    return SearchTracesResponse(trace_summaries, next_page_token)
