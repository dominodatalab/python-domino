from domino import Domino
import os

domino = Domino("marks/quick-start",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

domino_run = domino.runs_start(["main.py", "a", "b", "9"],
                               title="Started from Python API example code")
print(domino_run)

run_status = domino.runs_status(domino_run.get("runId"))
print(run_status)
