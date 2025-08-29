import pytest
import threading
from unittest.mock import call

def test_domino_run_dev(setup_mlflow_tracking_server, mocker, mlflow, tracing, logging):
        """
        DominoRun will contain the ai system configuration loggged as parameters and the summary metrics for its
                evaluation traces which are attached to the run only,
                and a logged model with the ai system configuration,
                and a default summarization metrics are computed for the evaluation traces

                the sklearn autolog function will be called
        """
        # must import logging from the module instead of the package
        # so that mocker works
        create_external_model_spy = mocker.spy(mlflow, "create_external_model")
        exp = mlflow.set_experiment("test_domino_run")

        @tracing.add_tracing(name="add_numbers", autolog_frameworks=['sklearn'], evaluator=lambda inputs, outputs: { 'add_numbers': outputs })
        def add_numbers(x, y):
                return x + y

        run_id = None
        with logging.DominoRun() as run:
                run_id = run.info.run_id
                add_numbers(1, 1)
                add_numbers(2, 2)

        # verify logged model created only once
        assert create_external_model_spy.call_count == 1, "create external model should be called once"

        models = mlflow.search_logged_models(experiment_ids=[exp.experiment_id], output_format='list')

        assert len(models) == 1

        model = models[0]
        # verify ai system config added as configuration
        assert model.params['chat_assistant.max_tokens'] == '1500'
        assert model.params['chat_assistant.model'] == 'gpt-3.5-turbo'
        assert model.params['chat_assistant.temperature'] == '0.7'
        assert model.params['version'] == '1.0'

        # verify evaluation traces not logged to model
        ts = mlflow.search_traces(experiment_ids=[exp.experiment_id], model_id=model.model_id, return_type='list')
        assert len(ts) == 0, "traces should not be logged to model"

        run = mlflow.get_run(run_id)

        # verify run has ai system config logged to it as parameters
        assert run.data.params['chat_assistant.max_tokens'] == '1500'
        assert run.data.params['chat_assistant.model'] == 'gpt-3.5-turbo'
        assert run.data.params['chat_assistant.temperature'] == '0.7'
        assert run.data.params['version'] == '1.0'

        # verify run has summary metrics logged to it
        # average of outputs is 2 + 4/2 = 3
        assert run.data.metrics['domino.prog.metric.add_numbers'] == 3, "average of add_numbers should be 3"

def test_domino_run_dev_custom_aggregator(setup_mlflow_tracking_server, mlflow, tracing, logging):
        """
        DominoRun will contain custom summarizaiton metrics for eval traces
        """
        exp = mlflow.set_experiment("test_domino_run_custom_aggregator")

        @tracing.add_tracing(name="median", evaluator=lambda inputs, outputs: { 'median': outputs })
        def for_median(x):
                return x

        @tracing.add_tracing(name="mean", evaluator=lambda inputs, outputs: { 'mean': outputs })
        def for_mean(x):
                return x

        @tracing.add_tracing(name="stdev", evaluator=lambda inputs, outputs: { 'stdev': outputs })
        def for_stdev(x):
                return x

        @tracing.add_tracing(name="min", evaluator=lambda inputs, outputs: { 'min': outputs })
        def for_min(x):
                return x

        @tracing.add_tracing(name="max", evaluator=lambda inputs, outputs: { 'max': outputs })
        def for_max(x):
                return x

        summarization_metrics = [
                ('median', 'median'),
                ('mean', 'mean'),
                ('stdev', 'stdev'),
                ('min', 'min'),
                ('max', 'max')
        ]
        run_id = None
        with logging.DominoRun(custom_summary_metrics=summarization_metrics) as run:
                run_id = run.info.run_id
                for i in range(1, 6):
                        for_median(i)
                        for_mean(i)
                        for_stdev(i)
                        for_min(i)
                        for_max(i)

        run = mlflow.get_run(run_id)

        # verify run has summary metrics logged to it
        # mean of outputs is 2 + 4/2 = 3
        # median is 2, 2, 4 = 2
        assert run.data.metrics['domino.prog.metric.median'] == 3
        assert run.data.metrics['domino.prog.metric.mean'] == 3
        assert run.data.metrics['domino.prog.metric.stdev'] == 1.581
        assert run.data.metrics['domino.prog.metric.min'] == 1
        assert run.data.metrics['domino.prog.metric.max'] == 5

def test_domino_run_dev_bad_custom_aggregator(setup_mlflow_tracking_server, mlflow, tracing, logging):
        """
        DominoRun will fail if one of the aggregators is invalid
        """
        exp = mlflow.set_experiment("test_domino_run_dev_bad_custom_aggregator")

        summarization_metrics = [('max', 'sdf')]

        with pytest.raises(ValueError):
                logging.DominoRun(custom_summary_metrics=summarization_metrics)

def test_domino_run_configure_experiment_name(setup_mlflow_tracking_server, mlflow, logging, tracing):
        """
        if an experiment name is provided, the DominoRun will create a run in that experiment
        and log traces to it
        """
        mlflow.create_experiment("test_domino_run_configure_experiment_name")
        exp_id = mlflow.create_experiment("test_domino_run_configure_experiment_name_other")

        @tracing.add_tracing(name="unit")
        def unit(x):
                return x

        run_id = None
        with logging.DominoRun("test_domino_run_configure_experiment_name_other") as run:
                run_id = run.info.run_id
                unit(1)

        run = mlflow.get_run(run_id)

        traces = mlflow.search_traces(experiment_ids=[exp_id], filter_string=f"trace.name = 'unit'")

        assert run.info.experiment_id == exp_id, "run should belong to test_domino_run_configure_experiment_name_other"
        assert len(traces) == 1

def test_domino_run_extend_current_run(setup_mlflow_tracking_server, mlflow, logging, tracing):
        """
        if a run_id is provided, then the DominoRun with add traces to that run
        """
        mlflow.set_experiment("test_domino_run_extend_current_run")

        @tracing.add_tracing(name="unit")
        def unit(x):
                return x

        run_id = None
        mlflow_run = None
        mlflow_run_id = None
        with mlflow.start_run() as mlflow_run:
                mlflow_run_id = mlflow_run.info.run_id
                with logging.DominoRun(run_id=mlflow_run_id) as run:
                        run_id = run.info.run_id
                        unit(1)


        traces = mlflow.search_traces(experiment_ids=[mlflow_run.info.experiment_id], filter_string=f"trace.name = 'unit'")

        assert run_id == mlflow_run_id
        assert len(traces) == 1

        # should have an external model linked to it
        models = mlflow.search_logged_models(experiment_ids=[mlflow_run.info.experiment_id], output_format='list')
        assert [m.source_run_id for m in models] == [mlflow_run_id]

def test_domino_run_should_not_swallow_exceptions(setup_mlflow_tracking_server, mlflow, logging):
        """
        If the user's code raises an exception, the DominoRun should allow user code to catch it
        """
        mlflow.set_experiment("test_domino_run_should_not_swallow_exceptions")

        with pytest.raises(ZeroDivisionError):
            with logging.DominoRun() as run:
                1/0

def test_domino_run_parallelized_logic(setup_mlflow_tracking_server, mlflow, logging, tracing):
        """
        Logic run in threads should execute normally
        """
        mlflow.set_experiment("test_domino_run_parallelized_logic")

        @tracing.add_tracing(name="a")
        def a(num):
                return num

        @tracing.add_tracing(name="b")
        def b(num):
                return num

        run = None
        with logging.DominoRun() as run:
                t1 = threading.Thread(target=a, args=(10,))
                t2 = threading.Thread(target=b, args=(10,))

                t1.start()
                t2.start()

                t1.join()
                t2.join()

        traces_a = mlflow.search_traces(filter_string=f"metadata.sourceRun = '{run.info.run_id}' AND trace.name = 'a'")
        traces_b = mlflow.search_traces(filter_string=f"metadata.sourceRun = '{run.info.run_id}' AND trace.name = 'b'")
