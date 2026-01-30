"""
To run these tests you need to have at least configured airflow in
local mode and run:

`airflow db init`
"""
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from airflow.operators.empty import EmptyOperator

from domino.airflow import DominoOperator
from domino.exceptions import RunFailedException
from airflow import DAG


TEST_PROJECT = os.environ.get("DOMINO_TEST_PROJECT")
dag_id = "test_operator"


def test_airflow_dags():
    pytest.importorskip("airflow")

    from airflow import DAG

    start_time = datetime.now()

    dag = DAG(dag_id, start_date=start_time, schedule=timedelta(days=1))
    task = EmptyOperator(
        dag=dag,
        task_id='test_airflow_dags',
    )

    task.execute(context={})


@patch("domino.airflow._operator.Domino")
def test_operator(mock_domino):
    mock_client = MagicMock()
    mock_client.runs_start_blocking.return_value = {"runId": "abc123", "status": "Succeeded"}
    mock_client.get_run_log.return_value = []
    mock_domino.return_value = mock_client

    start_time = datetime.now()

    dag = DAG(dag_id, start_date=start_time, schedule=timedelta(days=1))
    task = DominoOperator(
        dag=dag,
        task_id="test_operator",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -V"],
    )

    task.execute(context={})

    mock_domino.assert_called_once()
    mock_client.runs_start_blocking.assert_called_once()


@patch("domino.airflow._operator.Domino")
def test_operator_fail(mock_domino):
    mock_client = MagicMock()
    mock_client.runs_start_blocking.side_effect = RunFailedException("Run failed")
    mock_domino.return_value = mock_client

    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt, schedule=timedelta(days=1))
    task = DominoOperator(
        dag=dag,
        task_id="test_operator_fail",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -c 'import sys; sys.exit(1)'"],
    )

    with pytest.raises(RunFailedException):
        task.execute(context={})


@patch("domino.airflow._operator.Domino")
def test_operator_fail_invalid_tier(mock_domino):
    mock_client = MagicMock()
    mock_client.hardware_tiers_list.return_value = [
        {"hardwareTier": {"name": "small"}},
        {"hardwareTier": {"name": "medium"}},
    ]
    mock_domino.return_value = mock_client

    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt, schedule=timedelta(days=1))
    task = DominoOperator(
        dag=dag,
        task_id="test_operator_fail_invalid_tier",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -V"],
        tier="this tier does not exist",
    )

    with pytest.raises(ValueError):
        task.execute(context={})
