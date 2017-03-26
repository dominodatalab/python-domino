from domino import Domino
import pandas as pd
import json
import os

output_dir = "results"

# connect to domino; be sure to have these environment variables set
#  (runs inside a Domino executor automatically set these for you)
domino = Domino("nick/winequality",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])
raw_runs = domino.runs_list()['data']

# print number of runs to STDOUT
print("Details of {0} runs received").format(len(raw_runs))

# create results directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# write API out to all_runs.json
f = open('{0}/all_runs.json'.format(output_dir), 'w')
f.write(json.dumps(raw_runs))

# collect all runs into an array of dictionaries
all_runs = []
for run in raw_runs:
  # flatten diagnosticStatistics
  # *which are stored in a nested array of dictionaries)
    if run['diagnosticStatistics'] is not None:
        for stat in run['diagnosticStatistics'].get('data', []):
            stat_key = 'diagnosticStatistics.{0}'.format(stat['key'])
            run[stat_key] = stat['value']
        run['diagnosticStatistics.isError'] = run['diagnosticStatistics'].get(
            'isError', None)
    # delete diagnosticStatistics - we extracted all the value from it up above
    del run['diagnosticStatistics']
    # add run to array
    all_runs.append(run)

# create a dataframe with the flattened data
all_runs_df = pd.DataFrame(all_runs)

# convert epoch timestamps to human-readable format 'YYYY-MM-DD HH:MM:SS.SSS'
for field in ['queued', 'started', 'completed', 'postProcessedTimestamp']:
    all_runs_df['{0}_human'.format(field)] = \
        pd.to_datetime(all_runs_df[field], unit='ms')

# calculate some metrics in milliseconds
all_runs_df['millisecondsInQueue'] = all_runs_df.started - all_runs_df.queued
all_runs_df['millisecondsInExecution'] = \
    all_runs_df.completed - all_runs_df.started

# write dataframe to a CSV
all_runs_df.to_csv('{0}/all_runs.csv'.format(output_dir), index=False)

print("Finished exporting run information to {0}/all_runs.json \
      and {0}/all_runs.csv".format(output_dir))
