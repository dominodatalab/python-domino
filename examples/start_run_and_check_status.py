from domino import Domino
import os

domino = Domino("marks/quick-start",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

# Blocking: this will start the run and wait for the run to finish before returning the status of the run
domino_run = domino.runs_start_blocking(["main.py", "a", "b", "9"],
                               title="Started from Python API example code")
print(domino_run)


# Non-blocking: this will start the run and print the Run ID and check the status of the run *once*
# domino_run = domino.runs_start(["main.py", "a", "b", "9"],
#                                title="Started from Python API example code")
# print(domino_run)
# run_status = domino.runs_status(domino_run.get("runId"))
# print(run_status)
