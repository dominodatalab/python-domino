from domino import Domino
import os

domino = Domino("marks/quick-start",
                api_key=os.environ['RC_DOMINO_USER_API_KEY'],
                host=os.environ['RC_DOMINO_API_HOST'])

new_project = domino.project_create("marks", "fromapi")
print(new_project)
