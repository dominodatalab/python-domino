import os
from datetime import datetime

import pytest

from domino.airflow import DominoOperator

TEST_PROJECT = os.environ.get("DOMINO_TEST_PROJECT")


def test_my_operator():
    """
    To run this test you need to have at least configured airflow in
    local mode and run:

    `airflow initdb`
    """
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
