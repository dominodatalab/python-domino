from domino import Domino
import os
import time

domino = Domino(project=os.environ['PROJECT_NAME'],
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

# From all the environments, choose the first globally visible one
all_available_environments = domino.environments_list()
global_environments = list(filter(
    lambda x: x.get('visibility') == 'Global',
    all_available_environments['data']))
chosen_environment_id = global_environments[0].get('id')

# From all the models, choose one
all_available_models = domino.models_list()
print("This project \
      has {} models".format(len(all_available_models.get('data', []))))


# Get model versions
def describe_model_versions(model_id):
    model_ersions = domino.model_versions_get(model_id)
    print("Model {} \
        has {} versions:".format(model_id,
                                 len(model_versions.get('data', []))))
    print(model_versions)


# Publish a brand new model
num_models = int(os.environ['NUMBER_MODEL'])
for i in range(num_models):
    model_name = "Model published from API  : " + str(i)
    model_description = "desc " + str(i)
    published_model = domino.model_publish(file="main.R", function="api_endpoint",
                                           environment_id=chosen_environment_id,
                                           name=model_name,
                                           description=model_description)
    published_model_id = published_model.get('data', {}).get('_id')
    print("Model {} published, details below:".format(published_model_id))
    print(published_model)

    time.sleep(2)

    num_model_versions = int(os.environ['NUMBER_MODEL_VERSION'])
    for j in range(num_model_versions):
        model_version_description = "version " + str(j)
        # describe_model_versions(published_model_id)

        # Publlish another version for this model
        another_model_version = domino.model_version_publish(model_id=published_model_id,
                                                             file="main.R",
                                                             function="api_endpoint",
                                                             environment_id=chosen_environment_id,
                                                             description=model_version_description)

        describe_model_versions(published_model_id)

        time.sleep(2)v
