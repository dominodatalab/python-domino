import pytest

from domino.agents._eval_tags import InvalidEvaluationLabelException
from .mlflow_fixtures import fixture_create_traces

def test_log_evaluation_dev(setup_mlflow_tracking_server, mlflow, logging):
	# create experiment
	exp = mlflow.set_experiment("test_log_evaluation")

	fixture_create_traces()

	# log evaluations to traces
	traces = mlflow.search_traces(experiment_ids=[exp.experiment_id], filter_string="trace.name = 'test_add'", return_type='list')
	for trace in traces:
		logging.log_evaluation(
			trace.info.trace_id,
			value=1,
			name="helpfulness",
		)
		logging.log_evaluation(
			trace.info.trace_id,
			value="dogs",
			name="category",
		)

	# verify tags on traces
	tagged_traces = mlflow.search_traces(experiment_ids=[exp.experiment_id], filter_string="trace.name = 'test_add'", return_type="list")
	tags = tagged_traces[0].info.tags

	assert tags['domino.prog.label.category'] == 'dogs'
	assert tags['domino.prog.metric.helpfulness'] == '1'
	assert tags['domino.internal.is_eval'] == 'true'

def test_log_evaluation_invalid_name(setup_mlflow_tracking_server, mlflow, logging):
	# create experiment
	exp = mlflow.set_experiment("test_log_evaluation_invalid_name")

	fixture_create_traces()

	# log evaluations to traces
	traces = mlflow.search_traces(experiment_ids=[exp.experiment_id], filter_string="trace.name = 'test_add'", return_type='list')
	trace = traces[0]

	with pytest.raises(InvalidEvaluationLabelException):
		logging.log_evaluation(
			trace.info.trace_id,
			value=1,
			name="*",
		)

def test_log_evaluation_non_string_float(setup_mlflow_tracking_server, mlflow, logging):
	"""
	Log evaluation should not allow logging objects
	"""
	# create experiment
	exp = mlflow.set_experiment("test_log_evaluation_non_string_float")

	fixture_create_traces()

	# log evaluations to traces
	traces = mlflow.search_traces(experiment_ids=[exp.experiment_id], filter_string="trace.name = 'test_add'", return_type='list')
	trace = traces[0]

	with pytest.raises(TypeError):
		logging.log_evaluation(
			trace.info.trace_id,
			value={},
			name="myobject",
		)
