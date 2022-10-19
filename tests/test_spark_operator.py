"""
To run these tests you need to have at least configured airflow in
local mode and run:

`airflow initdb`
"""
import os
from datetime import datetime
from airflow import DAG
from airflow.models import TaskInstance
import pytest
from pprint import pformat

from domino.airflow import DominoSparkOperator
from domino.exceptions import RunFailedException
from domino.helpers import domino_is_reachable

TEST_PROJECT = os.environ.get("DOMINO_SPARK_TEST_PROJECT")


SPARK_ENVIRONMENT_ID = os.environ.get("DOMINO_SPARK_TEST_ENVIRONMENT_ID")


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_no_cluster():
    execution_dt = datetime.now()

    dag = DAG(dag_id="foo", start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        command="test_spark.py",
    )
    task.run()
    ti = TaskInstance(task=task, execution_date=execution_dt)
    task.execute(ti.get_template_context())


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_with_cluster(spark_environment_id):

    execution_dt = datetime.now()
    dag = DAG(dag_id="foo", start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        command="test_spark.py",
        on_demand_spark_cluster_properties={
            "computeEnvironmentId": spark_environment_id,
            "executorCount": 3,
        },
    )
    task.run()
    ti = TaskInstance(task=task, execution_date=execution_dt)
    task.execute(ti.get_template_context())


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_no_cluster_failed():
    execution_dt = datetime.now()

    dag = DAG(dag_id="foo", start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="foo",
        project=TEST_PROJECT,
        command="test_spark_fail.sh",
    )

    with pytest.raises(RunFailedException):
        task.run()
        ti = TaskInstance(task=task, execution_date=execution_dt)
        task.execute(ti.get_template_context())
