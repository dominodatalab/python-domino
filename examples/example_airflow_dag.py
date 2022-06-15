from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable

from domino.airflow import DominoOperator

api_key = Variable.get("DOMINO_USER_API_KEY")
host = Variable.get("DOMINO_API_HOST")

default_args = {
    "owner": "domino",
    "depends_on_past": False,
    "start_date": datetime(2019, 6, 5),
    "retries": 1,
    "retry_delay": timedelta(minutes=0.5),
}

dag = DAG(
    "domino_pipeline",
    description="Execute Airflow DAG in Domino",
    default_args=default_args,
    schedule_interval=timedelta(days=1),
)

t1 = DominoOperator(
    task_id="hello_world",
    api_key=api_key,
    host=host,
    project="weaton/domino-test",
    isDirect=True,
    dag=dag,
    command=["python -V"],
)
