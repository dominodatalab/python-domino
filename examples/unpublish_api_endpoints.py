from domino import Domino
import os

projects = ["marks/quick-start-fork"]

for project in projects:
    domino = Domino(project,
                    api_key=os.environ['DOMINO_USER_API_KEY'],
                    host=os.environ['DOMINO_API_HOST'])
    state = domino.endpoint_state()
    if state.get('isPublished', False):
        if domino.endpoint_unpublish():
            print("Successfully unpublished API endpoint for {}".format(
                project))
    else:
        print("There was no endpoint published for {}".format(project))
