from domino import Domino
import os

domino = Domino("marks/quick-start",
                api_key=os.environ['RC_DOMINO_USER_API_KEY'],
                host=os.environ['RC_DOMINO_API_HOST'])

try:
    new_project = domino.project_create("marks", "fromapi")
    print(new_project)
except:
    print("Could not create new project; it probably already exists")
    pass

# Create a new domino object, this time connected to the new project
domino = Domino("marks/fromapi",
                api_key=os.environ['RC_DOMINO_USER_API_KEY'],
                host=os.environ['RC_DOMINO_API_HOST'])

collaborators = domino.collaborators_get()
print(collaborators)
