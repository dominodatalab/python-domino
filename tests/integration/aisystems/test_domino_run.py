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
        assert run.data.metrics['mean_add_numbers'] == 3, "average of add_numbers should be 3"

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
        assert run.data.metrics['median_median'] == 3
        assert run.data.metrics['mean_mean'] == 3
        assert run.data.metrics['stdev_stdev'] == 1.581
        assert run.data.metrics['min_min'] == 1
        assert run.data.metrics['max_max'] == 5

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

        @tracing.add_tracing(name="unit", evaluator=lambda inputs, outputs: { 'unit': outputs })
        def unit(x):
                return x

        first_run_id = None
        second_run_id = None

        with logging.DominoRun() as run:
                first_run_id = run.info.run_id
                unit(1)

        with logging.DominoRun(run_id=first_run_id) as run:
                second_run_id = run.info.run_id
                unit(2)

        traces = mlflow.search_traces(experiment_ids=[run.info.experiment_id], filter_string=f"metadata.mlflow.sourceRun = '{first_run_id}'", return_type='list')

        assert first_run_id == second_run_id, "Both runs should have the same run_id"
        assert len(traces) == 2, "There should be two traces for unit"

        # each domino run should have an external model linked to it
        models = mlflow.search_logged_models(experiment_ids=[run.info.experiment_id], output_format='list')
        assert [m.source_run_id for m in models] == [first_run_id, first_run_id]

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

        with logging.DominoRun():
                t1 = threading.Thread(target=a, args=(10,))
                t2 = threading.Thread(target=b, args=(10,))

                t1.start()
                t2.start()

                t1.join()
                t2.join()

        traces_a = mlflow.search_traces(filter_string="trace.name = 'a'", return_type='list')
        traces_b = mlflow.search_traces(filter_string="trace.name = 'b'", return_type='list')
        def get_run_id(trace):
                return trace.info.trace_metadata.get('mlflow.sourceRun')

        assert len(traces_a) == 1, "There should be one trace for a"
        assert len(traces_b) == 1, "There should be one trace for b"
        assert get_run_id(traces_a[0]) == get_run_id(traces_b[0]), "The a and b traces should belong to the same run"

def test_domino_run_extend_concluded_run_manual_evals_mean_logged(setup_mlflow_tracking_server, mlflow, tracing, logging):
        """
        When extending a concluded run, manual log_evaluation calls inside the DominoRun block
        are summarized and the average metric is logged to the run.
        """
        mlflow.set_experiment("test_domino_run_extend_concluded_run_manual_evals_mean_logged")

        @tracing.add_tracing(name="add_numbers")
        def add_numbers(x, y):
                return x + y

        # Create and conclude a run with two traces (outputs: 2 and 4)
        with mlflow.start_run() as parent_run:
                concluded_run_id = parent_run.info.run_id
                add_numbers(1, 1)
                add_numbers(2, 2)

        # Extend the concluded run and log manual evaluations; DominoRun should log mean summary (3)
        with logging.DominoRun(run_id=concluded_run_id):
                traces_resp = tracing.search_traces(run_id=concluded_run_id, trace_name="add_numbers")
                for t in traces_resp.data:
                        # use the function output as the evaluation value
                        value = t.spans[0].outputs
                        logging.log_evaluation(
                                trace_id=t.id,
                                name="helpfulness",
                                value=value,
                        )

        run = mlflow.get_run(concluded_run_id)
        # average of 2 + 4 = 3
        assert run.data.metrics['mean_helpfulness'] == 3, "average of helpfulness should be 3"

def test_domino_run_extend_concluded_run_manual_evals_custom_aggregator_logged(setup_mlflow_tracking_server, mlflow, tracing, logging):
        """
        When extending a concluded run, with a custom aggregator, manual log_evaluation calls inside the
        DominoRun block are summarized using the custom aggregator and logged to the run.
        """
        mlflow.set_experiment("test_domino_run_extend_concluded_run_manual_evals_custom_aggregator_logged")

        @tracing.add_tracing(name="add_numbers")
        def add_numbers(x, y):
                return x + y

        # Create and conclude a run with two traces (outputs: 2 and 4)
        with mlflow.start_run() as parent_run:
                concluded_run_id = parent_run.info.run_id
                add_numbers(1, 1)
                add_numbers(2, 2)

        # Extend the concluded run and log manual evaluations; DominoRun should log custom summary (max -> 4)
        custom_summary_metrics = [("helpfulness", "max")]
        with logging.DominoRun(run_id=concluded_run_id, custom_summary_metrics=custom_summary_metrics):
                traces_resp = tracing.search_traces(run_id=concluded_run_id, trace_name="add_numbers")
                for t in traces_resp.data:
                        value = t.spans[0].outputs
                        logging.log_evaluation(
                                trace_id=t.id,
                                name="helpfulness",
                                value=value,
                        )

        run = mlflow.get_run(concluded_run_id)
        # max of 2 and 4 is 4
        assert run.data.metrics['max_helpfulness'] == 4, "max of helpfulness should be 4"

def test_domino_run_recomputes_existing_aggregations(setup_mlflow_tracking_server, mlflow, tracing, logging):
        """
        When a run already has aggregated metrics (e.g., max_<metric>), a subsequent DominoRun
        on the same run_id recomputes those aggregations in addition to defaults.
        """
        exp = mlflow.set_experiment("test_domino_run_recomputes_existing_aggregations")

        @tracing.add_tracing(name="agg", evaluator=lambda inputs, outputs: { 'agg': outputs })
        def agg_fn(x):
                return x

        run_id = None
        # First run computes both default mean and custom max aggregations
        with logging.DominoRun(custom_summary_metrics=[('agg', 'mean'), ('agg', 'max')]) as run:
                run_id = run.info.run_id
                agg_fn(1)
                agg_fn(3)


        run = mlflow.get_run(run_id)
        assert run.data.metrics['mean_agg'] == 2, 'mean should be 2'
        assert run.data.metrics['max_agg'] == 3, 'max should be 3'

        # Second run continues the same run and adds a new value; expects recomputed max (and mean)
        with logging.DominoRun(run_id=run_id) as run2:
                agg_fn(5)

        run = mlflow.get_run(run_id)
        assert run.data.metrics['max_agg'] == 5, 'max should be 5'
        assert run.data.metrics['mean_agg'] == 3, 'mean should be 3'
