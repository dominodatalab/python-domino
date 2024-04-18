"""
To run these tests you need to have at least configured airflow in
local mode and run:

`airflow db init`
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
dag_id = "test_spark_operator"

@pytest.mark.skipif(os.getenv("SPARK_DEP") != "yes", reason="Extra dependency required")
@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_no_cluster():
    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="test_spark_operator_no_cluster",
        project=TEST_PROJECT,
        command="test_spark.py",
    )
    task.run()
    ti = TaskInstance(task=task, execution_date=execution_dt)
    task.execute(ti.get_template_context())

@pytest.mark.skipif(os.getenv("SPARK_DEP") != "yes", reason="Extra dependency required")
@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_with_cluster(spark_cluster_env_id):

    execution_dt = datetime.now()
    dag = DAG(dag_id, start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="test_spark_operator_with_cluster",
        project=TEST_PROJECT,
        command="test_spark.py",
        on_demand_spark_cluster_properties={
            "computeEnvironmentId": spark_cluster_env_id,
            "executorCount": 3,
        },
    )
    task.run()
    ti = TaskInstance(task=task, execution_date=execution_dt)
    task.execute(ti.get_template_context())

@pytest.mark.skipif(os.getenv("SPARK_DEP") != "yes", reason="Extra dependency required")
@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_with_compute_cluster_properties(spark_cluster_env_id):
    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="test_spark_operator_with_compute_cluster_properties",
        project=TEST_PROJECT,
        command="test_spark.py",
        compute_cluster_properties={
            "clusterType": "Spark",
            "computeEnvironmentId": spark_cluster_env_id,
            "masterHardwareTierId": "small-k8s",
            "workerHardwareTierId": "small-k8s",
            "workerCount": 3,
        },
    )
    task.run()
    ti = TaskInstance(task=task, execution_date=execution_dt)
    task.execute(ti.get_template_context())

@pytest.mark.skipif(os.getenv("SPARK_DEP") != "yes", reason="Extra dependency required")
@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_spark_operator_no_cluster_failed():
    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt)
    task = DominoSparkOperator(
        dag=dag,
        task_id="test_spark_operator_no_cluster_failed",
        project=TEST_PROJECT,
        command="test_spark_fail.sh",
    )

    with pytest.raises(RunFailedException):
        task.run()
        ti = TaskInstance(task=task, execution_date=execution_dt)
        task.execute(ti.get_template_context())
