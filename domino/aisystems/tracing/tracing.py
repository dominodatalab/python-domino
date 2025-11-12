from dataclasses import dataclass
from datetime import datetime
import functools
import inspect
import logging
import mlflow
from typing import Optional, Callable, Any
from uuid import uuid4

from .._client import client
from .inittracing import init_tracing, triggered_autolog_frameworks, call_autolog
from ..logging.logging import log_evaluation
from ._util import get_is_production, build_ai_system_experiment_name
from .._eval_tags import validate_label, get_eval_tag_name
from .._verify_domino_support import verify_domino_support

EvalResult = dict[str, int | float | str]

SpanEvaluator = Callable[[mlflow.entities.Span], EvalResult]
TraceEvaluator = Callable[[mlflow.entities.Trace], EvalResult]

DOMINO_NO_RESULT_ADD_TRACING = "domino_no_result"

@dataclass
class SpanSummary:
    """A span in a trace."""

    id: str
    """the mlflow ID of the span"""

    name: str
    """The name of the span"""

    trace_id: str
    """The parent trace ID"""

    inputs: Any
    """The inputs to the function that created the span"""

    outputs: Any
    """The outputs of the function that created the span"""

@dataclass
class EvaluationResult:
    """An evaluation result for a trace."""

    name: str
    """The name of the evaluation"""

    value: float | str
    """The value of the evaluation"""


@dataclass
class TraceSummary:
    """A summary of a trace."""

    name: str
    """The name of the trace"""

    id: str
    """The mlflow ID of the trace"""

    spans: list[SpanSummary]
    """The child spans of this trace"""

    evaluation_results: list[EvaluationResult]
    """The evaluation results for this trace"""


@dataclass
class SearchTracesResponse:
    """The response from searching for traces."""

    data: list[TraceSummary]
    """The list of trace summaries"""

    page_token: Optional[str]
    """The token for the next page of results"""


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
    evaluator: Optional[SpanEvaluator] = None,
    trace_evaluator: Optional[TraceEvaluator] = None,
    is_production: bool = False,
    allow_evaluator_autologging: bool = False,
) -> Optional[dict]:
    if not is_production and evaluator or trace_evaluator:
        if not allow_evaluator_autologging:
            # disable all autologging
            for fw in triggered_autolog_frameworks:
                call_autolog(fw, disable=True)

        span_eval_result = None
        trace_eval_result = None

        # get span evaluator result
        if evaluator:
            try:
                span_eval_result = evaluator(span)
            except Exception as e:
                logger.error(
                    "Inline evaluation failed for evaluator, %s. Error: %s",
                    evaluator.__name__,
                    e,
                    exc_info=True,
                )

        # get trace evaluator result
        if trace_evaluator:
            try:
                trace = mlflow.get_trace(span.trace_id)
            except Exception as e:
                logger.warning(
                    "A trace_evaluator %s was provided, but the trace could not be found: %s",
                    trace_evaluator.__name__,
                    e,
                )
                trace = None

            if trace:
                try:
                    trace_eval_result = trace_evaluator(trace)
                except Exception as e:
                    logger.error(
                        "Inline evaluation failed for trace_evaluator, %s. Error: %s",
                        trace_evaluator.__name__,
                        e,
                        exc_info=True,
                    )

            else:
                # warn the user if they provided a trace evaluator, but we couldn't find a trace
                # because they may need to design their evaluations differently
                logger.warning(
                    "A trace_evaluator %s was provided, but the trace could not be found",
                    trace_evaluator.__name__,
                )

        if not allow_evaluator_autologging:
            enable_evaluator_logging()

        # if at least one result exists, return a combined dict
        # otherwise, return none
        if span_eval_result or trace_eval_result:
            return {**(trace_eval_result or {}), **(span_eval_result or {})}

    # enable eval logging here as well just in case we didn't do any evaluations
    # because no eval result generated
    if not allow_evaluator_autologging:
        enable_evaluator_logging()

    return None

def enable_evaluator_logging():
    # re-enable autologging if it was previously enabled
    for fw in triggered_autolog_frameworks:
        call_autolog(fw)

def _log_eval_results(
    parent_span: mlflow.entities.Span,
    evaluator: Optional[SpanEvaluator],
    trace_evaluator: Optional[TraceEvaluator],
    allow_evaluator_autologging: bool,
):
    """
    Saves the evaluation results
    """
    is_production = get_is_production()
    eval_result = _do_evaluation(parent_span, evaluator, trace_evaluator, is_production, allow_evaluator_autologging)

    if eval_result:
        for k, v in eval_result.items():
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
    inputs = {
        k: v for k, v in bound_args.arguments.items() if k != "self" and k != "cls"
    }
    parent_span.set_inputs(inputs)

    return inputs


def add_tracing(
    name: str,
    autolog_frameworks: Optional[list[str]] = [],
    evaluator: Optional[SpanEvaluator] = None,
    trace_evaluator: Optional[TraceEvaluator] = None,
    eagerly_evaluate_streamed_results: bool = True,
    allow_tracing_evaluator: bool = False,
):
    """This is a decorator that starts an mlflow span for the function it decorates. If there is an existing trace
    a span will be appended to it. If there is no existing trace, a new trace will be created.

    It also enables the user to run evaluators when the code is run in development mode. Evaluators can be run on
    the span and/or trace generated for the wrapped function call. The trace evaluator will run if the parent trace
    was started and finished by the related decorator call. The trace will contain all child span information.
    The span evaluator will always run. The evaluation results from both evaluators will be combined and saved
    to the trace.

    This decorator must be used directly on the function to be traced without any intervening decorators, because it
    must have access to the arguments.

    @add_tracing(
        name="assistant_chat_bot",
        evaluator=evaluate_helpfulness,
    )
    def ask_chat_bot(user_input: str) -> dict:
        ...

    Args:
        name: the name of the span to add to existing trace or create if no trace exists yet.

        autolog_frameworks: an optional list of mlflow supported frameworks to autolog

        evaluator: an optional function that takes the span created for the wrapped function and returns a dictionary of evaluation results. The evaluation results will be saved to the trace

        trace_evaluator: an optional function that takes the trace for this call stack and returns a dictionary of evaluation results. This evaluator will be triggered if the trace was started and finished by the add tracing decorator. The evaluation results will be saved to the trace

        eagerly_evaluate_streamed_results: optional boolean, defaults to true, this determines if all
            yielded values should be aggregated and set as outputs to a single span. This makes evaluation easier, but
            will impact performance if you expect a large number of streamed values. If set to false, each yielded value
            will generate a new span on the trace, which can be evaluated post-hoc. Inline evaluators won't be executed.
            Each span will have a group_id set in their attributes to indicate that they are part of the same function call.
            Each span will have an index to indicate what order they arrived in.

        allow_tracing_evaluator: optional boolean, defaults to false. This determines if inline evaluators
            will be traced by mlflow autolog.

    Returns:
        A decorator that wraps the function to be traced.
    """
    validate_label(name)


    def decorator(func):
        # For Regular Functions (e.g., langgraph_agents.run_agent)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = DOMINO_NO_RESULT_ADD_TRACING
            init_tracing(autolog_frameworks)

            with mlflow.start_span(name) as parent_span:
                _set_span_inputs(parent_span, func, args, kwargs)

                result = func(*args, **kwargs)

                parent_span.set_outputs(result)

            if result != DOMINO_NO_RESULT_ADD_TRACING:
                _log_eval_results(parent_span, evaluator, trace_evaluator, allow_tracing_evaluator)

            return _return_traced_result(result)

        # for async functions
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = DOMINO_NO_RESULT_ADD_TRACING
                init_tracing(autolog_frameworks)

                with mlflow.start_span(name) as parent_span:
                    _set_span_inputs(parent_span, func, args, kwargs)

                    result = await func(*args, **kwargs)

                    parent_span.set_outputs(result)

                if result != DOMINO_NO_RESULT_ADD_TRACING:
                    _log_eval_results(parent_span, evaluator, trace_evaluator, allow_tracing_evaluator)

                return _return_traced_result(result)

            return async_wrapper

        # For Generator Functions (e.g., RAGAgent.answer)
        if inspect.isgeneratorfunction(func):

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                result = DOMINO_NO_RESULT_ADD_TRACING
                init_tracing(autolog_frameworks)

                with mlflow.start_span(name) as parent_span:
                    inputs = _set_span_inputs(parent_span, func, args, kwargs)

                    result = func(*args, **kwargs)

                    if not eagerly_evaluate_streamed_results:
                        # can't do inline evaluation, so warn if an evaluator is provided
                        if evaluator or trace_evaluator:
                            logger.warning(
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
                                gen_span.set_attributes(
                                    {"group_id": str(group_id), "index": i}
                                )
                                yield v
                                gen_span.set_outputs(v)
                    else:
                        # get all results and set as outputs
                        all_results = [v for v in result]
                        parent_span.set_outputs(all_results)
                        for v in all_results:
                            yield v

                if eagerly_evaluate_streamed_results and result != DOMINO_NO_RESULT_ADD_TRACING:
                    _log_eval_results(parent_span, evaluator, trace_evaluator, allow_tracing_evaluator)

            return wrapper

        return wrapper

    return decorator


def _build_evaluation_result(tag_key: str, tag_value: str) -> EvaluationResult:
    value = tag_value
    try:
        value = float(tag_value)
    except Exception:
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
                evaluation_results=[
                    _build_evaluation_result(key, value)
                    for (key, value) in trace.info.tags.items()
                    if get_eval_tag_name(key) is not None
                ],
            )
        )

    return trace_summaries


def search_ai_system_traces(
    ai_system_id: str,
    ai_system_version: Optional[str] = None,
    trace_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page_token: Optional[str] = None,
    max_results: Optional[int] = None,
) -> SearchTracesResponse:
    """This allows searching for traces that have a certain name and returns a paginated response of trace summaries that
    include the spans that were requested.

    Args:
        ai_system_id: string, the ID of the AI System to filter by
        ai_system_version: string, the version of the AI System to filter by, if not provided will search throuh all versions
        trace_name: the name of the traces to search for
        start_time: python datetime
        end_time: python datetime, defaults to now
        page_token: page token for pagination. You can use this to request the next page of results and may
         find a page_token in the response of the previous search_traces call.
        max_results: defaults to 100

    Returns:
        SearchTracesResponse: a token based pagination response that contains a list of trace summaries
            data: list of TraceSummary
            page_token: the next page's token
    """
    return _search_traces(
        None,
        ai_system_id,
        ai_system_version,
        trace_name,
        start_time,
        end_time,
        page_token,
        max_results,
    )


def search_traces(
    run_id: str,
    trace_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page_token: Optional[str] = None,
    max_results: Optional[int] = None,
) -> SearchTracesResponse:
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
    return _search_traces(
        run_id,
        None,
        None,
        trace_name,
        start_time,
        end_time,
        page_token,
        max_results,
    )


def _search_traces(
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

    if not run_id and not ai_system_version and not ai_system_id:
        raise Exception(
            "Either run_id or ai_system_id and ai_system_version must be provided to search traces"
        )

    if ai_system_version and not ai_system_id:
        raise Exception(
            "If ai_system_version is provided, ai_system_id must also be provided"
        )

    filter_clauses = []

    # get experiment id
    if run_id:
        experiment_id = client.get_run(run_id).info.experiment_id
        run_filter_clause = f'metadata.mlflow.sourceRun = "{run_id}"'
        filter_clauses.append(run_filter_clause)
    else:
        experiment_name = build_ai_system_experiment_name(ai_system_id)
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            raise Exception(
                f"No experiment found for ai_system_id: {ai_system_id} and ai_system_version: {ai_system_version}"
            )
        experiment_id = experiment.experiment_id

        # add prod trace tag filters
        if ai_system_id:
            filter_clauses.append(f'tags.mlflow.domino.app_id = "{ai_system_id}"')

        if ai_system_version:
            filter_clauses.append(
                f'tags.mlflow.domino.app_version_id = "{ai_system_version}"'
            )

    if start_time or end_time:
        time_range_filter_clause = ""

        if start_time:
            start_ms = _datetime_to_ms(start_time)
            time_range_filter_clause += f"timestamp_ms > {start_ms}"

        if end_time:
            end_ms = _datetime_to_ms(end_time)
            time_range_filter_clause += f" AND timestamp_ms < {end_ms}"

        if start_time and end_time and start_time >= end_time:
            logger.warning("start_time must be before end_time")

        filter_clauses.append(time_range_filter_clause)

    if trace_name:
        trace_name_filter_clause = f'trace.name = "{trace_name}"'
        filter_clauses.append(trace_name_filter_clause)

    # get traces made within the time range
    # get traces with the trace names
    filter_string = " AND ".join([x for x in filter_clauses if x])

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

def _return_traced_result(result: any):
    if result != DOMINO_NO_RESULT_ADD_TRACING:
        return result
    else:
        logger.warning("No result returned from traced function")

logger = logging.getLogger(__name__)
