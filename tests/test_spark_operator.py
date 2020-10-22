"""
To run these tests you need to have at least configured airflow in
local mode and run:

`airflow initdb`
"""
import os
from datetime import datetime

import pytest
import logging
from domino.airflow import DominoSparkOperator 
from domino.exceptions import RunFailedException

TEST_PROJECT = os.environ.get("DOMINO_SPARK_TEST_PROJECT")
SPARK_ENVIRONMENT_ID = os.environ.get('DOMINO_SPARK_TEST_ENVIRONMENT_ID')


def test_spark_operator_no_cluster():
    airflow = pytest.importorskip("airflow")

    from airflow import DAG
    from airflow.models import TaskInstance

    dag = DAG(dag_id="foo", start_date=datetime.now())
    task = DominoSparkOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        command="test_spark.py",
    )
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())


def test_spark_operator_with_cluster():
    airflow = pytest.importorskip("airflow")

    from airflow import DAG
    from airflow.models import TaskInstance

    dag = DAG(dag_id="foo", start_date=datetime.now())
    task = DominoSparkOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        command="test_spark.py",
        on_demand_spark_cluster_properties={
            "computeEnvironmentId": SPARK_ENVIRONMENT_ID,
            "executorCount": 3
        }
    )
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())
