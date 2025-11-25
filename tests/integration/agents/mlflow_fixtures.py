from datetime import datetime, timedelta
import pytest
import os
from unittest.mock import patch
from typing import Callable, Optional

from domino.agents._client import client
from domino.agents.tracing._util import build_agent_experiment_name
from .conftest import TEST_AGENTS_ENV_VARS
from .test_util import reset_prod_tracing

def fixture_create_traces():
        pytest.importorskip("mlflow")
        import mlflow
        @mlflow.trace(name="test_add")
        def test_add(x, y):
                return x + y

        # create traces
        with mlflow.start_run():
                test_add(1, 2)

def add_prod_tags(traces: Optional[list], agent_id: str, agent_version: str):
        # adds prod tags to traces, simulating what domino services would do in a prod deployment

        pytest.importorskip("mlflow")
        import mlflow
        if not traces:
                exp_name = build_agent_experiment_name(agent_id)
                exp = mlflow.get_experiment_by_name(exp_name)

                traces = mlflow.search_traces(experiment_ids=[exp.experiment_id], return_type='list')

        for t in traces:
                client.set_trace_tag(t.info.trace_id, "mlflow.domino.app_id", agent_id)
                client.set_trace_tag(t.info.trace_id, "mlflow.domino.app_version_id", agent_version)

def create_span_at_time(name: str, inputs: int, hours_ago: int, experiment_id: str):
        pytest.importorskip("mlflow")
        import mlflow

        dt = datetime.now() - timedelta(hours=hours_ago)
        ns = int(dt.timestamp() * 1e9)
        span = mlflow.start_span_no_context(name=name, inputs=inputs, experiment_id=experiment_id, start_time_ns=ns)
        span.end()

def fixture_create_prod_traces(
        agent_id: str,
        agent_version: str,
        trace_name: str,
        tracing,
        hours_ago: Optional[int] = None, # also used as input value for span
):
        """Creates prod agent traces with a specific trace name"""
        pytest.importorskip("mlflow")
        import mlflow

        reset_prod_tracing()

        @tracing.add_tracing(name=trace_name)
        def one(x):
                return x

        env_vars = TEST_AGENTS_ENV_VARS | {"DOMINO_AGENT_IS_PROD": "true", "DOMINO_APP_ID": agent_id }
        with patch.dict(os.environ, env_vars, clear=True):
                tracing.init_tracing()
                if hours_ago is not None:
                        experiment = mlflow.get_experiment_by_name(build_agent_experiment_name(agent_id))
                        create_span_at_time(trace_name, hours_ago, hours_ago, experiment.experiment_id)
                else:
                        one(1)

                exp_name = build_agent_experiment_name(agent_id)
                exp = mlflow.get_experiment_by_name(exp_name)

                ts = mlflow.search_traces(experiment_ids=[exp.experiment_id], filter_string=f"trace.name = '{trace_name}'", return_type='list')

                # add prod tags (would be done by Domino deployment)
                add_prod_tags(ts, agent_id, agent_version)
