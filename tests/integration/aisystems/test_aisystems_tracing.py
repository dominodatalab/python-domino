from datetime import datetime, timedelta
import inspect
import logging
import os
import pytest
import threading
import time
from unittest.mock import call, patch

from ...conftest import TEST_AI_SYSTEMS_ENV_VARS
from .mlflow_fixtures import fixture_create_prod_traces, create_span_at_time
from domino.aisystems._client import client
from domino.aisystems.tracing._util import build_ai_system_experiment_name
from domino.aisystems._eval_tags import InvalidEvaluationLabelException

def test_init_tracing_prod(setup_mlflow_tracking_server, mocker, mlflow, tracing):
        """
        should initialize autologging only once for each framework
        should create an experiment for the ai system and tag it only once
        """
        app_id = "appid"
        test_case_vars = {"DOMINO_AI_SYSTEM_IS_PROD": "true", "DOMINO_APP_ID": app_id}
        expected_experiment_name = build_ai_system_experiment_name(app_id)
        env_vars = TEST_AI_SYSTEMS_ENV_VARS | test_case_vars

        import domino.aisystems.tracing.tracing
        import domino.aisystems._client
        import mlflow
        autolog_spy = mocker.spy(domino.aisystems.tracing.inittracing, "call_autolog")
        set_experiment_tag_spy = mocker.spy(domino.aisystems._client.client, "set_experiment_tag")
        set_experiment_spy = mocker.spy(mlflow, "set_experiment")

        with patch.dict(os.environ, env_vars, clear=True):
                tracing.init_tracing(["sklearn"])
                tracing.init_tracing(["sklearn"])
                found_exp = mlflow.get_experiment_by_name(expected_experiment_name)

                assert autolog_spy.call_args_list == [call('sklearn')]
                assert set_experiment_tag_spy.call_count == 1, "should only save tag on experiment once"
                assert set_experiment_spy.call_count is not 0, "should set an active experiment"
                assert found_exp is not None, "ai system experiment should exist"
                assert found_exp.tags.get("ai_system") == "true", "ai system experiment should be tagged"

def test_init_tracing_logs_experiment_creation_debug(setup_mlflow_tracking_server, mlflow, tracing, caplog):
        """
        when log level is debug, verify the experiment creation log includes the experiment ID
        """
        app_id = "app_id_logs_debug"
        test_case_vars = {"DOMINO_AI_SYSTEM_IS_PROD": "true", "DOMINO_APP_ID": app_id}
        env_vars = TEST_AI_SYSTEMS_ENV_VARS | test_case_vars

        with patch.dict(os.environ, env_vars, clear=True), caplog.at_level(logging.DEBUG):
                tracing.init_tracing(should_reinitialize=True)
                expected_experiment_name = build_ai_system_experiment_name(app_id)
                exp = mlflow.get_experiment_by_name(expected_experiment_name)
                assert exp is not None, "experiment should be created in prod mode"
                assert f"Created experiment for AI System with ID {exp.experiment_id}" in caplog.text

def test_logging_traces_prod(setup_mlflow_tracking_server, mocker, mlflow, tracing):
        """
        traces created in separate threads forked from the same main thread
        should be saved to the same ai system experiment
        """
        app_id = "threaded_app_id"
        test_case_vars = {"DOMINO_AI_SYSTEM_IS_PROD": "true", "DOMINO_APP_ID": app_id}
        expected_experiment_name = build_ai_system_experiment_name(app_id)
        env_vars = TEST_AI_SYSTEMS_ENV_VARS | test_case_vars

        with patch.dict(os.environ, env_vars, clear=True):
                tracing.init_tracing(should_reinitialize=True)

                @tracing.add_tracing(name="a")
                def a(num):
                        return num

                @tracing.add_tracing(name="b")
                def b(num):
                        return num

                t1 = threading.Thread(target=a, args=(10,))
                t2 = threading.Thread(target=b, args=(10,))

                t1.start()
                t2.start()

                t1.join()
                t2.join()

        # a and b traces should all be in the ai system experiment
        traces_a = mlflow.search_traces(filter_string="trace.name = 'a'", return_type='list')
        traces_b = mlflow.search_traces(filter_string="trace.name = 'b'", return_type='list')

        def get_experiment_id(trace):
                return trace.info.trace_location.mlflow_experiment.experiment_id

        found_exp_ids = set([get_experiment_id(t) for t in traces_a + traces_b])
        actual_exp_id = set([mlflow.get_experiment_by_name(expected_experiment_name).experiment_id])
        assert found_exp_ids == actual_exp_id, "traces should be linked to the ai system experiment"


def test_init_tracing_dev_mode(setup_mlflow_tracking_server, mocker, mlflow, tracing):
        """
        should not create an experiment or set tags
        """
        import domino.aisystems._client
        import mlflow
        set_experiment_tag_spy = mocker.spy(domino.aisystems._client.client, "set_experiment_tag")
        set_experiment_spy = mocker.spy(mlflow, "set_experiment")

        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS, clear=True):
                tracing.init_tracing(["sklearn"])

                assert set_experiment_tag_spy.call_count == 0, "should set experiment tag"
                assert set_experiment_spy.call_count == 0, "should not set an active experiment"

def test_add_tracing_dev(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        """
        add_tracing will create a new trace with a given name
        and attach evaluation tags to the trace
        """
        # must import logging from the module instead of the package
        # so that mocker works
        exp = mlflow.set_experiment("test_add_tracing_dev")

        @tracing.add_tracing(name="add_numbers", autolog_frameworks=["sklearn"], evaluator=lambda inputs, outputs: { 'result': outputs })
        def add_numbers(x, y):
                return x + y

        with logging.DominoRun("test_add_tracing_dev"):
                add_numbers(1, 1)

        ts = mlflow.search_traces(experiment_ids=[exp.experiment_id], return_type='list')
        assert len(ts) == 1, "only one trace should be created"

        # assert tags
        tags = ts[0].info.tags
        assert tags['domino.prog.metric.result'] == '2'
        assert tags['domino.internal.is_eval'] == 'true'

def test_add_tracing_invalid_label(setup_mlflow_tracking_server, tracing):
        with pytest.raises(InvalidEvaluationLabelException):
                @tracing.add_tracing(name="*")
                def unit(x):
                        return x

def test_add_tracing_dev_no_evaluator(setup_mlflow_tracking_server, mlflow, tracing, logging):
        """
        add_tracing will create a new trace not add evaluations
        """
        exp = mlflow.set_experiment("test_add_tracing_dev_no_evaluator")

        @tracing.add_tracing(name="add_numbers")
        def add_numbers(x, y):
                return x + y

        with logging.DominoRun("test_add_tracing_dev_no_evaluator"):
                add_numbers(1, 1)

        # assert tags
        ts = mlflow.search_traces(experiment_ids=[exp.experiment_id], return_type='list')
        tags = ts[0].info.tags

        assert 'domino.internal.is_eval' not in tags

def test_add_tracing_decorator_preserves_function_info(setup_mlflow_tracking_server, tracing):
        def func_with_args(a: int, b: int, c: int=10, *args, **kwargs):
                """Function with various parameter types."""
                return a + b + c

        @tracing.add_tracing(name="decorated_func")
        def decorated_func(a: int, b: int, c: int=10, *args, **kwargs):
                """returns the input value"""
                return a + b + c

        original_sig = inspect.signature(func_with_args)
        decorated_sig = inspect.signature(decorated_func)

        assert decorated_func.__name__ == "decorated_func", "the function name should be preserved by the decorator"
        assert decorated_func.__doc__ == "returns the input value", "the function docstring should be preserved by the decorator"
        assert decorated_func.__module__ == "tests.integration.aisystems.test_aisystems_tracing"
        assert decorated_sig == original_sig
        assert list(decorated_sig.parameters.keys()) == ['a', 'b', 'c', 'args', 'kwargs']
        assert decorated_sig.parameters['c'].default == 10
        assert decorated_sig.parameters['a'].annotation == int

def test_add_tracing_preseves_self_and_cls(setup_mlflow_tracking_server, tracing):
        """
        add_tracing should preserve self and cls for functionality of the decorated method
        """
        class MyClass:
                class_value = 2
                def __init__(self):
                        self.value = 1

                @tracing.add_tracing(name="instance_method")
                def instance_method(self, x):
                        return self.value + x

                @classmethod
                @tracing.add_tracing(name="class_method")
                def class_method(cls, x):
                        return cls.class_value + x

        obj = MyClass()

        assert obj.instance_method(1) == 2
        assert MyClass.class_method(1) == 3

def test_add_tracing_arguments_passed_to_span(setup_mlflow_tracking_server, tracing, mlflow):
        """
        add_tracing should preserve self and cls for functionality of the decorated method,
        but should not pass them as inputs to the trace.

        it should pass args and kwargs as inputs, also
        it should pass default values
        """
        exp = mlflow.set_experiment("test_add_tracing_arguments_passed_to_span")
        experiment_id = exp.experiment_id

        class MyClass:
                @tracing.add_tracing(name="instance_method")
                def instance_method(self, x):
                        return x

                @classmethod
                @tracing.add_tracing(name="class_method")
                def class_method(cls, x):
                        return x

        @tracing.add_tracing(name="args_kwargs")
        def args_kwargs(*args, **kwargs):
                return (args, kwargs)

        @tracing.add_tracing(name="fun_with_defaults")
        def fun_with_defaults(x=10):
                return x

        obj = MyClass()
        obj.instance_method(1)
        MyClass.class_method(1)
        args_kwargs(1, y=2)
        fun_with_defaults()


        instance_trace = mlflow.search_traces(experiment_ids=[experiment_id], return_type='list', filter_string="trace.name = 'instance_method'")[0]
        class_trace = mlflow.search_traces(experiment_ids=[experiment_id], return_type='list', filter_string="trace.name = 'class_method'")[0]
        args_kwargs_trace = mlflow.search_traces(experiment_ids=[experiment_id], return_type='list', filter_string="trace.name = 'args_kwargs'")[0]
        fun_with_defaults_trace = mlflow.search_traces(experiment_ids=[experiment_id], return_type='list', filter_string="trace.name = 'fun_with_defaults'")[0]

        def get_inputs(trace):
                return trace.data.spans[0].inputs

        it_inputs = get_inputs(instance_trace)
        assert it_inputs == {'x': 1}

        ct_inputs = get_inputs(class_trace)
        assert ct_inputs == {'x': 1}

        ak_inputs = get_inputs(args_kwargs_trace)
        assert ak_inputs == {'args': [1], 'kwargs': {'y': 2}}

        d_inputs = get_inputs(fun_with_defaults_trace)
        assert d_inputs == {'x': 10}

def test_add_tracing_failed_inline_evaluator_logs_warning(setup_mlflow_tracking_server, tracing, mlflow, caplog):
        """
        if the inline evaluator fails, a warning is logged and the main code still executes
        """
        mlflow.set_experiment("test_add_tracing_failed_inline_evaluator_logs_warning")

        def failing_evaluator(i, o):
                return 1/0

        @tracing.add_tracing(name="unit", evaluator=failing_evaluator)
        def unit(x):
                return x

        with mlflow.start_run(), caplog.at_level(logging.WARNING):
                assert unit(1) == 1
                assert "Inline evaluation failed for evaluator, failing_evaluator" in caplog.text

def test_add_tracing_works_with_generator(setup_mlflow_tracking_server, tracing, mlflow):
        """
        add_tracing should not record all result from a generator if not specified
        if we don't eagerly load the reults onto one trace, we save a span for each yield
        """
        exp = mlflow.set_experiment("test_add_tracing_works_with_generator")
        experiment_id = exp.experiment_id

        @tracing.add_tracing(name="gen", evaluator=lambda i, o: { 'result': 1 }, eagerly_evaluate_streamed_results=False)
        def gen():
                for i in range(3):
                        yield i

        xs = [x for x in gen()]
        assert xs == [0, 1, 2], "Results should be unaffected by tracing"

        gen_trace = mlflow.search_traces(experiment_ids=[experiment_id], return_type='list', filter_string="trace.name = 'gen'")[0]
        assert len(gen_trace.data.spans) == 4, "should have 4 spans, one for function call, and one for each yield"
        assert [s.outputs for s in gen_trace.data.spans[1:]] == [0, 1, 2], "yields spans should have correct outputs"
        assert ["group_id" in s.attributes for s in gen_trace.data.spans[1:]] == [True, True, True], "yields spans should have a group_id attribute"
        assert [s.attributes["index"] for s in gen_trace.data.spans[1:]] == [0, 1, 2]
        assert len(set([s.attributes["group_id"] for s in gen_trace.data.spans[1:]])) == 1, "group_id should be the same for all yields"

        # assert evaluation didn't happen inline
        tags = gen_trace.info.tags
        assert 'domino.prog.metric.result' not in tags
        assert 'domino.internal.is_eval' not in tags

def test_add_tracing_works_with_eagerly_evaluated_generator(setup_mlflow_tracking_server, tracing, mlflow):
        """
        add_tracing should record the result from a generator and evaluate it inline
        """
        exp = mlflow.set_experiment("test_add_tracing_works_with_eagerly_evaluated_generator")
        experiment_id = exp.experiment_id

        @tracing.add_tracing(name="gen_record_all", evaluator=lambda i, o: { 'result': 1 })
        def gen_record_all():
                for i in range(3):
                        yield i

        xs = [x for x in gen_record_all()]
        assert xs == [0, 1, 2]

        gen_trace = mlflow.search_traces(experiment_ids=[experiment_id], return_type='list', filter_string="trace.name = 'gen_record_all'")[0]
        span = gen_trace.data.spans[0]
        tags = gen_trace.info.tags

        assert len(gen_trace.data.spans) == 1
        assert span.outputs == [0, 1, 2]
        assert tags['domino.prog.metric.result'] == '1'
        assert tags['domino.internal.is_eval'] == 'true'

@pytest.mark.asyncio
async def test_add_tracing_works_with_async(setup_mlflow_tracking_server, mlflow, tracing):
        exp = mlflow.set_experiment("test_add_tracing_works_with_async")

        @tracing.add_tracing(name="async_function", evaluator=lambda i, o: { 'result': 1 })
        async def async_function(x):
                return x

        res = await async_function(1)
        assert res == 1

        traces = mlflow.search_traces(experiment_ids=[exp.experiment_id], return_type='list')

        assert [t.data.spans[0].inputs for t in traces] == [{'x':1}], "Inputs to trace should be the function arguments"
        assert [t.data.spans[0].outputs for t in traces] == [1], "Outputs to trace should be the function return value"

def test_search_traces(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        @tracing.add_tracing(name="unit")
        def unit(x):
                return x

        @tracing.add_tracing(name="parent", evaluator=lambda i, o: {'mymetric': 1, 'mylabel': 'category'})
        def parent(x, y):
                return unit(x) + unit(y)

        @tracing.add_tracing(name="parent2")
        def parent2(x):
                return x

        mlflow.set_experiment("test_search_traces")
        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                parent(1, 2)
                parent2(1)

        res = tracing.search_traces(run_id=run_id)
        span_data = [(s.name, s.inputs, s.outputs) for trace in res.data for s in trace.spans]

        assert sorted([trace.name for trace in res.data]) == sorted(["parent", "parent2"])
        assert sorted([(t.name, t.value) for trace in res.data for t in trace.evaluation_results if trace.name == "parent"]) \
                == sorted([("mylabel", "category"), ("mymetric", 1.0)])
        assert sorted(span_data) == sorted([("parent", {'x':1, 'y': 2}, 3), \
                ("parent2", {'x':1}, 1), ("unit_1", {'x':1}, 1), ("unit_2", {'x':2}, 2)
        ])

def test_search_traces_by_trace_name(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        @tracing.add_tracing(name="unit")
        def unit(x):
                return x

        @tracing.add_tracing(name="parent")
        def parent(x, y):
                return unit(x) + unit(y)

        @tracing.add_tracing(name="parent2")
        def parent2(x):
                return x

        mlflow.set_experiment("test_search_traces_by_trace_name")
        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                parent(1, 2)
                parent2(1)

        res = tracing.search_traces(run_id=run_id, trace_name="parent")
        span_data = [(s.name, s.inputs, s.outputs) for trace in res.data for s in trace.spans]

        assert [trace.name for trace in res.data] == ["parent"]
        assert sorted(span_data) == sorted([("parent", {'x':1, 'y': 2}, 3), ("unit_1", {'x':1}, 1), ("unit_2", {'x':2}, 2)])

def test_search_traces_by_timestamp(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        @tracing.add_tracing(name="parent")
        def parent(x):
                return x

        mlflow.set_experiment("test_search_traces_by_timestamp")
        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                parent(1)

                time.sleep(2)

                parent(2)

                time.sleep(2)

                parent(3)

        start_time = datetime.now() - timedelta(seconds=4)
        end_time = datetime.now() - timedelta(seconds=2)

        res = tracing.search_traces(
                run_id=run_id,
                trace_name="parent",
                start_time=start_time,
                end_time=end_time
        )

        assert [trace.name for trace in res.data] == ["parent"]
        assert [[(s.name, s.inputs['x'], s.outputs) for s in trace.spans] for trace in res.data] == [[("parent", 2, 2)]]

def test_search_traces_with_traces_made_2hrs_ago(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        exp = mlflow.set_experiment("test_search_traces_with_traces_made_2hrs_ago")

        def parent(x):
                dt = datetime.now() - timedelta(hours=2)
                ns = int(dt.timestamp() * 1e9)
                span = mlflow.start_span_no_context(name="parent",  inputs=1, experiment_id=exp.experiment_id, start_time_ns=ns)
                span.end()
                return x

        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                parent(1)

        res = tracing.search_traces(
                run_id=run_id,
                trace_name="parent",
        )

        assert [trace.name for trace in res.data] == ["parent"]

        # If i shorten the time filter, I get no results
        recent_res = tracing.search_traces(
                run_id=run_id,
                trace_name="parent",
                start_time=datetime.now() - timedelta(hours=1),
        )
        assert recent_res.data == []

def test_search_traces_multiple_runs_in_exp(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        exp = mlflow.set_experiment("test_search_traces_multiple_runs_in_exp")

        @tracing.add_tracing(name="unit1")
        def unit1(x):
                return x

        @tracing.add_tracing(name="unit2")
        def unit2(x):
                return x

        run_1_id = None
        with logging.DominoRun() as run:
                run_1_id = run.info.run_id
                unit1(1)

        with logging.DominoRun() as run:
                unit2(1)

        res = tracing.search_traces(run_id=run_1_id)

        assert [trace.name for trace in res.data] == ["unit1"]

def test_search_traces_ai_system(setup_mlflow_tracking_server_no_env_var_mock, mlflow, tracing):
        """
        Can filter by ai system id alone or id and version
        """
        app_id = "test_search_traces_ai_system_id"
        app_version_1 = "test_search_traces_ai_system_version_1"
        app_version_2 = "test_search_traces_ai_system_version_2"

        fixture_create_prod_traces(app_id, app_version_1, "one", tracing)
        fixture_create_prod_traces(app_id, app_version_2, "two", tracing)

        def get_trace_names(traces):
                return sorted([trace.name for trace in traces.data])

        all_traces = tracing.search_traces(ai_system_id=app_id)
        assert get_trace_names(all_traces) == ["one", "two"], "Can get traces for all ai system versions"

        v1_traces = tracing.search_traces(ai_system_id=app_id, ai_system_version=app_version_1)
        assert get_trace_names(v1_traces) == ["one"], "Can get traces for just ai system version 1"

        v2_traces = tracing.search_traces(ai_system_id=app_id, ai_system_version=app_version_2)
        assert get_trace_names(v2_traces) == ["two"], "Can get traces for just ai system version 2"

def test_search_traces_ai_system_ai_system_id_required(setup_mlflow_tracking_server_no_env_var_mock, tracing):
        """
        ai system id is required if version supplied
        """

        with pytest.raises(Exception) as e_info:
                tracing.search_traces(ai_system_version="fakeversion")

        assert "ai_system_id must also be provided" in str(e_info), "Should raise if version provided without id"

def test_search_traces_no_run_ai_system_ids_supplied(setup_mlflow_tracking_server_no_env_var_mock, tracing):
        """
        should throw if no run id, ai system version, or id supplied
        """

        with pytest.raises(Exception) as e_info:
                tracing.search_traces()

        assert "Either run_id or ai_system_id and ai_system_version must be provided to search traces" in str(e_info), \
                "Should raise no ai system info or run info provided"

def test_search_traces_filters_should_work_together_dev(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        """
        When every filter is specified as well as pagination, the expected results should be returned
        The test creates multiple differently named traces over the course of a few hours in an experiment
        with multiple runs
        """
        exp = mlflow.set_experiment("test_search_traces_filters_should_work_together_dev")

        @tracing.add_tracing(name="unit1")
        def unit1(x):
                return x

        def create_span_at_time(name: str, inputs: int, hours_ago: int):
                dt = datetime.now() - timedelta(hours=hours_ago)
                ns = int(dt.timestamp() * 1e9)
                span = mlflow.start_span_no_context(name=name, inputs=inputs, experiment_id=exp.experiment_id, start_time_ns=ns)
                span.end()

        @tracing.add_tracing(name="sum1")
        def sum1(x, y):
                return x + y

        @tracing.add_tracing(name="unit2")
        def unit2(x):
                return x

        run_1_id = None
        with logging.DominoRun() as run:
                run_1_id = run.info.run_id

                create_span_at_time(name="sum1", inputs=1, hours_ago=5)

                # search_traces should return the following two spans
                create_span_at_time(name="sum1", inputs=2, hours_ago=3)
                create_span_at_time(name="sum1", inputs=3, hours_ago=2)

                unit1(1)

        with logging.DominoRun() as run:
                unit2(1)

        start_time = datetime.now() - timedelta(hours=4)
        end_time = datetime.now() - timedelta(hours=1)

        def get_traces(next_page_token):
                return tracing.search_traces(
                        run_id=run_1_id,
                        trace_name="sum1",
                        start_time=start_time,
                        end_time=end_time,
                        page_token=next_page_token,
                        max_results=1
                )

        def get_span_data(page):
                return [(trace.name, [s.inputs for s in trace.spans]) for trace in page.data]

        # should only return the first sum1 call in the run_1_id domino run
        page1 = get_traces(None)
        assert get_span_data(page1) == [("sum1", [2])], "Should return first call"

        # should only return the second sum1 call in the run_1_id domino run
        page2 = get_traces(page1.page_token)
        assert get_span_data(page2) == [("sum1", [3])], "Should return second call"


def test_search_traces_filters_should_work_together_prod(setup_mlflow_tracking_server_no_env_var_mock, mocker, mlflow, tracing, logging):
        """
        When searching by ai system ID and version and when every filter is specified as well as pagination,
        the expected results should be returned
        The test creates multiple differently named traces over the course of a few hours in an experiment
        with multiple runs
        """
        app_id = "test_search_traces_filters_should_work_together_prod"
        app_version_1 = f"{app_id}_1"
        app_version_2 = f"{app_id}_2"

        fixture_create_prod_traces(app_id, app_version_1, "sum1", tracing, hours_ago=5)

        # search_traces should return the following two spans
        fixture_create_prod_traces(app_id, app_version_1, "sum1", tracing, hours_ago=2)
        fixture_create_prod_traces(app_id, app_version_1, "sum1", tracing, hours_ago=3)

        fixture_create_prod_traces(app_id, app_version_1, "unit1", tracing)
        fixture_create_prod_traces(app_id, app_version_2, "unit2", tracing)

        start_time = datetime.now() - timedelta(hours=4)
        end_time = datetime.now() - timedelta(hours=1)

        def get_traces(next_page_token):
                return tracing.search_traces(
                        ai_system_id=app_id,
                        ai_system_version=app_version_1,
                        trace_name="sum1",
                        start_time=start_time,
                        end_time=end_time,
                        page_token=next_page_token,
                        max_results=1
                )

        def get_span_data(page):
                return [(trace.name, [s.inputs for s in trace.spans]) for trace in page.data]

        # should only return the first sum1 call
        page1 = get_traces(None)
        assert get_span_data(page1) == [("sum1", [3])], "Should return first call"

        # should only return the second sum1 call
        page2 = get_traces(page1.page_token)
        assert get_span_data(page2) == [("sum1", [2])], "Should return second call"


def test_search_traces_pagination(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        """
        The api should provide a page token in if the total number of results is bigger than the max results
        and you can use that token to get the next page of results
        """
        @tracing.add_tracing(name="parent")
        def parent(x):
                return x

        mlflow.set_experiment("test_search_traces_by_timestamp")
        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                parent(1)
                parent(2)

        res1 = tracing.search_traces(
                run_id=run_id,
                max_results=1,
        )

        assert [[(s.name, s.inputs['x'], s.outputs) for s in trace.spans] for trace in res1.data] == [[("parent", 1, 1)]]

        res2 = tracing.search_traces(
                run_id=run_id,
                max_results=1,
                page_token=res1.page_token
        )

        assert [[(s.name, s.inputs['x'], s.outputs) for s in trace.spans] for trace in res2.data] == [[("parent", 2, 2)]]

def test_search_traces_from_lazy_generator(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        @tracing.add_tracing(name="parent", eagerly_evaluate_streamed_results=False)
        def parent():
                for i in range(3):
                        yield i

        mlflow.set_experiment("test_search_traces_from_lazy_generator")
        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                # traces don't emit unless you consume generator
                [x for x in parent()]

        traces = tracing.search_traces(
                run_id=run_id,
        )

        assert len(traces.data) == 1
        assert len(traces.data[0].spans) == 4


def test_init_tracing_triggers_two_get_experiment_by_name_calls_in_threads(setup_mlflow_tracking_server, mlflow, tracing):
        """
        init_tracing should call client.get_experiment_by_name twice
        when invoked concurrently from two threads.
        """
        app_id = "concurrency_app"
        env_vars = TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_AI_SYSTEM_IS_PROD": "true", "DOMINO_APP_ID": app_id}
        expected_experiment_name = build_ai_system_experiment_name(app_id)

        with patch.dict(os.environ, env_vars, clear=True):
                from domino.aisystems._client import client

                def send_traces():
                        tracing.init_tracing()

                        @tracing.add_tracing(name="do")
                        def do():
                                return 1

                        do()

                # Spy on the exact call site used inside init_tracing
                with patch.object(
                        client,
                        "get_experiment_by_name",
                        wraps=client.get_experiment_by_name,
                ) as spy_get_by_name:
                        t1 = threading.Thread(target=send_traces)
                        t2 = threading.Thread(target=send_traces)

                        t1.start()
                        t2.start()
                        t1.join()
                        t2.join()

                        # Both threads should trigger a lookup within init_tracing
                        assert spy_get_by_name.call_count == 2, "get_experiment_by_name should be called twice from init_tracing"

                # Verify two traces named "do" were saved to the AI System experiment
                exp = mlflow.get_experiment_by_name(expected_experiment_name)
                traces = mlflow.search_traces(
                        experiment_ids=[exp.experiment_id],
                        filter_string="trace.name = 'do'",
                        return_type='list',
                )
                assert len(traces) == 2, "Two traces named 'do' should be saved to the experiment"
