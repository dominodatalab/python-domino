import os
from datetime import datetime

import pytest
from airflow.operators.dummy import DummyOperator
from airflow import settings
from airflow.models.base import Base

from domino.airflow import DominoOperator
from domino.exceptions import RunFailedException
from domino.helpers import domino_is_reachable
from airflow import DAG
from airflow.models import TaskInstance


TEST_PROJECT = os.environ.get("DOMINO_TEST_PROJECT")
dag_id = "test_operator"


@pytest.fixture(autouse=True, scope="module")
def setup_airflow_db():
    Base.metadata.create_all(settings.engine)
    yield
    Base.metadata.drop_all(settings.engine)


def test_airflow_dags():
    pytest.importorskip("airflow")

    from airflow import DAG
    from airflow.models import TaskInstance

    start_time = datetime.now()

    dag = DAG(dag_id, start_date=start_time)
    task = DummyOperator(
        dag=dag,
        task_id='test_airflow_dags',
    )

    task.run()
    ti = TaskInstance(task=task, execution_date=start_time)
    task.execute(ti.get_template_context())


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_operator():
    start_time = datetime.now()

    dag = DAG(dag_id, start_date=start_time)
    task = DominoOperator(
        dag=dag,
        task_id="test_operator",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -V"],
    )

    task.run()
    ti = TaskInstance(task=task, execution_date=start_time)
    task.execute(ti.get_template_context())


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_operator_fail(caplog):
    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt)
    task = DominoOperator(
        dag=dag,
        task_id="test_operator_fail",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -c 'import sys; sys.exit(1)'"],
    )

    with pytest.raises(RunFailedException):
        task.run()
        ti = TaskInstance(task=task, execution_date=execution_dt)
        task.execute(ti.get_template_context())


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_operator_fail_invalid_tier(caplog):
    execution_dt = datetime.now()

    dag = DAG(dag_id, start_date=execution_dt)
    task = DominoOperator(
        dag=dag,
        task_id="test_operator_fail_invalid_tier",
        project=TEST_PROJECT,
        isDirect=True,
        command=["python -V"],
        tier="this tier does not exist",
    )

    with pytest.raises(ValueError):
        task.run()
        ti = TaskInstance(task=task, execution_date=execution_dt)
        task.execute(ti.get_template_context())
