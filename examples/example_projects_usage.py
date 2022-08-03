import os
from pprint import pprint

from domino import Domino
from domino.exceptions import ProjectNotFoundException

domino = Domino(
    "marks/quick-start",
    api_key=os.environ["DOMINO_USER_API_KEY"],
    host=os.environ["DOMINO_API_HOST"],
)

new_project_name = "fromapi3"

try:
    new_project = domino.project_create(new_project_name)
    print(new_project)
except ProjectNotFoundException:
    print("Could not create new project; it probably already exists")
    pass

# Create a new domino object, this time connected to the new project
domino = Domino(
    "marks/{}".format(new_project_name),
    api_key=os.environ["DOMINO_USER_API_KEY"],
    host=os.environ["DOMINO_API_HOST"],
)

collaborators = domino.collaborators_get()
print(collaborators)

new_collaborators = domino.collaborators_add("integration-test")
print(new_collaborators)

# get tags
tags = domino.tags_list()
pprint(tags)

domino.tags_add(["new", "old"])
domino.tags_add(["new", "old"])
tags = domino.tags_list()
pprint(tags)

domino.tags_remove("old")
tags = domino.tags_list()
pprint(tags)
