from domino import Domino
import os

domino = Domino("system-test/quick-start",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

raw_runs = domino.runs_list()['data']
print('Example run:'+str(raw_runs[0]))

raw_datasets = domino.datasets_list()['data']
print('Datasets:'+str(raw_datasets))