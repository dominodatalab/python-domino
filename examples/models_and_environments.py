from domino import Domino
import os

domino = Domino("marks/quick-start-fork",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

# From all the environments, choose the first globally visible one
all_available_environments = domino.environments_list()
global_environments = filter(
    lambda x: x.get('visibility') == 'Global',
    all_available_environments['data'])
print("This Domino deployment has {} gloabl environments".format(len(global_environments)))
chosen_environment_id = global_environments[0].get('id')
print("Environment chosen is {}".format(chosen_environment_id))

# From all the models, choose one
all_available_models = domino.models_list()
print("This project has {} models".format(len(all_available_models.get('data',[]))))