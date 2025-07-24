import mlflow
from typing import Optional, Callable, Any
from .._client import client
from ..logging.logging import log_evaluation, add_domino_tags

"""
When a user initializes Domino Logging, we will set this active model ID.
"""
global active_model_id
active_model_id = None

def _do_evaluation(
        span,
        evaluator: Optional[Callable[[Any, Any], dict[str, Any]]] = None,
        is_production: bool = False) -> Optional[dict]:

        if not is_production and evaluator:
            return evaluator(span.inputs, span.outputs)
        return None

# TODO make idemptotent,
# this is Haran's init domino tracing
# init the experiment and run in dev before this is called, prod is fine
# TODO rename to logging
def _init(frameworks: list[str] = []):
    """Initialize code based Domino tracing for an AI System component.
    If in dev mode, it is expected that a run has been intialized. All traces will be linked to that run and a
    LoggedModel will be created, which represents the AI System component and will contain the configuration
    defined in the ai_system_config.yaml.

    If in prod mode, a DOMINO_AI_SYSTEM_MODEL_ID is required and represents the production AI System
    component. All traces will be linked to that model. No run is required.

    Args:
        frameworks: list[string] of frameworks to autolog
    """

	# TODO find way to configure, probably not as a function argument
    ai_system_config_path = "./ai_system_config.yaml"
    is_production = _is_production()

    # set production environment variable
    os.environ["DOMINO_EVALUATION_LOGGING_IS_PROD"] = json.dumps(is_production)


    # NOTE: user provides the model name if they want to link traces to a
    # specific AI System. We will recommend this for production, but not for dev
    # evaluation
    if is_production:
        # if no active model, set the active model
        if not active_model_id:
            model = _get_prod_logged_model()
            mlflow.set_active_model(model_id=model.model_id)

            active_model_id = model.model_id
    else:
        if not active_model_id:
            # save configuration file for the AI System
            params = read_ai_system_config(ai_system_config_path)
            if mlflow.active_run():
                run_id = mlflow.active_run().info.run_id

                # TODO get single logged model?
                logged_models = mlflow.search_logged_models(
                    filter_string=f"source_run_id='{run_id}'",
                    output_format="list"
                )

                active_model_id = None
                if len(logged_models) > 0:
                    mlflow.set_active_model(model_id=logged_models[0].model_id)
                    active_model_id = logged_models[0].model_id
                else:
                    model = mlflow.create_external_model(
                        model_type="AI System",
                        params=params
                    )
                    mlflow.set_active_model(model_id=model.model_id)
                    active_model_id = model.model_id

    for fw in frameworks:
        try:
            getattr(mlflow, fw).autolog()
        except Exception as e:
            logging.warning(f"Failed to call mlflow autolog for {fw} ai framework", e)

def start_trace(
        name: str,
		frameworks: Optional[list[str]] = [],
        evaluator: Optional[Callable[[Any, Any], dict[str, Any]]] = None,
        extract_input_field: Optional[str] = None,
        extract_output_field: Optional[str] = None
    ):
    """A decorator that starts an mlflow trace for the function it decorates.
    It also enables the user to run an evaluation inline in the code is run in development mode on
    the inputs and outputs of the wrapped function call.
    The user can provide input and output formatters for formatting what's on the trace
    and the evaluation result inputs, which can be used by client's to extract relevant data when
    analyzing a trace.

    @start_domino_trace(
        name="assistant_chat_bot",
        evaluator=evaluate_helpfulness,
        extract_output_field="answer"
    )
    def ask_chat_bot(user_input: str) -> dict:
        ...

    Args:
        name: the name of the trace to create

        evaluator: an optional function that takes the inputs and outputs of the wrapped function and returns
        a dictionary of evaluation results. The evaluation result will be added to the trace as tags.

        extract_input_field: an optional dot separated string that specifies what subfield to access in the trace input

        extract_output_field: an optional dot separated string that specifies what subfield to access in the trace output

    Returns:
        A decorator that wraps the function to be traced.
    """
    def decorator(func):

        def wrapper(*args, **kwargs):
            _init(frameworks)

            is_production = _is_production()
            inputs = { 'args': args, 'kwargs': kwargs }

            parent_trace = client.start_trace(name, inputs=inputs)
            result = func(*args, **kwargs)
            client.end_trace(parent_trace.trace_id, outputs=result)

            # TODO error handling?
            trace = client.get_trace(parent_trace.trace_id).data.spans[0]

            eval_result = _do_evaluation(trace, evaluator, is_production)
            if eval_result:
                for (k, v) in eval_result.items():

                    # tag trace with the evaluation inputs, outputs, and result
                    # or maybe assessment?
                    log_evaluation(
                        trace,
                        eval_result_label=k,
                        eval_result=v,
                        extract_input_field=extract_input_field,
                        extract_output_field=extract_output_field
                    )
            else:
                add_domino_tags(trace, is_production, extract_input_field, extract_output_field, is_eval=False)

            return result

        return wrapper
    return decorator

def append_span(
        name: str,
		frameworks: Optional[list[str]] = [],
        evaluator: Optional[Callable[[Any, Any], dict[str, Any]]] = None,
        extract_input_field: Optional[str] = None,
        extract_output_field: Optional[str] = None
    ):
    """A decorator that starts an mlflow span for the function it decorates. If there is an existing trace
    this span will be appended to it.

    It also enables the user to run an evaluation inline in the code is run in development mode on
    the inputs and outputs of the wrapped function call.
    The user can provide input and output formatters for formatting what's on the trace
    and the evaluation result inputs, which can be used by client's to extract relevant data when
    analyzing a trace.

    @append_domino_span(
        name="assistant_chat_bot",
        evaluator=evaluate_helpfulness,
        extract_output_field="answer"
    )
    def ask_chat_bot(user_input: str) -> dict:
        ...

    Args:
        name: the name of the trace to create

        evaluator: an optional function that takes the inputs and outputs of the wrapped function and returns
        a dictionary of evaluation results. The evaluation result will be added to the trace as tags.

        extract_input_field: an optional dot separated string that specifies what subfield to access in the trace input

        extract_output_field: an optional dot separated string that specifies what subfield to access in the trace output

    Returns:
        A decorator that wraps the function to be traced.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            _init(frameworks)

            is_production = _is_production()
            with mlflow.start_span(name) as parent_span:
                inputs = { 'args': args, 'kwargs': kwargs }
                parent_span.set_inputs(inputs)
                result = func(*args, **kwargs)
                parent_span.set_outputs(result)

                eval_result = _do_evaluation(parent_span, evaluator, is_production)

                if eval_result:
                    for (k, v) in eval_result.items():
                        log_evaluation(
                            parent_span,
                            eval_result=v,
                            eval_result_label=k,
                            extract_input_field=extract_input_field,
                            extract_output_field=extract_output_field,
                        )
                else:
                    add_domino_tags(parent_span, is_production, extract_input_field, extract_output_field, is_eval=False)
                return result

        return wrapper
    return decorator
