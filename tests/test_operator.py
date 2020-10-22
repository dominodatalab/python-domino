"""
To run these tests you need to have at least configured airflow in
local mode and run:

`airflow initdb`
"""
import os
from datetime import datetime

import pytest
import logging
from domino.airflow import DominoOperator
from domino.exceptions import RunFailedException

TEST_PROJECT = os.environ.get("DOMINO_TEST_PROJECT")


def test_operator():
    airflow = pytest.importorskip("airflow")

    from airflow import DAG
    from airflow.models import TaskInstance

    dag = DAG(dag_id="foo", start_date=datetime.now())
    task = DominoOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -V"],
    )
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())


def test_operator_fail(caplog):
    airflow = pytest.importorskip("airflow")

    from airflow import DAG
    from airflow.models import TaskInstance

    dag = DAG(dag_id="foo", start_date=datetime.now())
    task = DominoOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -c 'import sys; sys.exit(1)'"],
    )
    ti = TaskInstance(task=task, execution_date=datetime.now())
    
    with pytest.raises(RunFailedException):
        task.execute(ti.get_template_context())


def test_operator_fail_invalid_tier(caplog):
    airflow = pytest.importorskip("airflow")

    from airflow import DAG
    from airflow.models import TaskInstance

    dag = DAG(dag_id="foo", start_date=datetime.now())
    task = DominoOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -V"],
        tier='this tier does not exist',
    )
    ti = TaskInstance(task=task, execution_date=datetime.now())
    
    with pytest.raises(ValueError):
        task.execute(ti.get_template_context())
