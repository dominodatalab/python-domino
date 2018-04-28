from domino import Domino
import os

domino = Domino("marks/empty",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

# From all the environments, choose the first globally visible one
all_environments_available = domino.environments_list()
global_environments = filter(
    lambda x: x.get('visibility') == 'Global',
    all_environments_available['data'])
environment_id = global_environments[0].get('id')

