from domino import Domino
import os

domino = Domino("marks/quick-start-fork",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

# From all the environments, choose the first globally visible one
all_available_environments = domino.environments_list()
global_environments = list(filter(
    lambda x: x.get('visibility') == 'Global',
    all_available_environments['data']))
print("This Domino deployment has \
      {} gloabl environments".format(len(global_environments)))
chosen_environment_id = global_environments[0].get('id')
print("Environment chosen is {}".format(chosen_environment_id))

# From all the models, choose one
all_available_models = domino.models_list()
print("This project \
      has {} models".format(len(all_available_models.get('data', []))))

# Publish a brand new model
published_model = domino.model_publish(file="main.R", function="api_endpoint",
                                       environment_id=chosen_environment_id,
                                       name="Model published from API!",
                                       description="v1")
published_model_id = published_model.get('data', {}).get('_id')
print("Model {} published, details below:".format(published_model_id))
print(published_model)

# Get model versions
def describe_model_versions(model_id):
    model_versions = domino.model_versions_get(model_id)
    print("Model {} \
        has {} versions:".format(model_id,
                                 len(model_versions.get('data', []))))
    print(model_versions)

describe_model_versions(published_model_id)

# Publlish another version for this model
another_model_version = domino.model_version_publish(model_id=published_model_id,
                                                     file="main.R",
                                                     function="api_endpoint",
                                                     environment_id=chosen_environment_id,
                                                     description="v2")

describe_model_versions(published_model_id)
