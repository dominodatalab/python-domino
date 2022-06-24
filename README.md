# python-domino

This library provides bindings for the [Domino Data Lab API](https://dominodatalab.github.io/api-docs/).

The latest released version is `1.0.8`.

## Version Compatibility Matrix

`python-domino` library is compatible with different versions of the `Domino`:

| Domino Versions |                                    Python-Domino                                    |
| --------------- | :---------------------------------------------------------------------------------: |
| 3.6.x or Lower  |      [0.3.5](http://github.com/dominodatalab/python-domino/archive/0.3.5.zip)       |
| 4.1.0 or Higher | [1.0.0](https://github.com/dominodatalab/python-domino/archive/1.0.0.zip) or Higher |

## Installation

Starting from version `1.0.6`, `python-domino` is available on PyPI as `dominodatalab`:

    pip install dominodatalab

If you are adding install instructions for `python-domino` to your [Domino Environment](https://support.dominodatalab.com/hc/en-us/articles/115000392643-Compute-Environment-Management) Dockerfile Instructions field, you must add `RUN` to the beginning:

    RUN pip install dominodatalab

To install specific version of the library from PyPI, for example, `1.0.6`, use the following command:

    pip install dominodatalab==1.0.6

To install specific version of the library from GitHub, for example, `1.0.6`, use the following command:

    pip install https://github.com/dominodatalab/python-domino/archive/1.0.6.zip

## Overview

### Setting up the connection

You can set up the connection by creating new instance of `Domino`.

<hr>

### _class_ Domino(project, api_key=None, host=None, domino_token_file=None, auth_token=None)

The parameters are:

- _project:_ A project identifier (in the form of ownerusername/projectname)
- _api_key:_ (Optional) An API key to authenticate with. If not provided the library will expect to find one
  in the DOMINO_USER_API_KEY environment variable.
- _host:_ (Optional) A host URL. If not provided the library will expect to find one in the DOMINO_API_HOST
  environment variable.
- _domino_token_file:_ (Optional) Path to domino token file containing auth token. If not provided the library will expect to find one
  in the DOMINO_TOKEN_FILE environment variable.
- _auth_token:_ (Optional) Authentication token

Note:

1. The authentication preference should always be given to the authentication token. If it's not passed, the path to domino token file
   takes precedence, otherwise the API key is used. If none of these three parameters are passed, then preference will be given to the
   domino token file from the corresponding environment variable, then to the API key from the corresponding environment variable.
2. By default the log level is set to `INFO`, to set log level to `DEBUG`, set `DOMINO_LOG_LEVEL` environment variable to `DEBUG`
<hr>

## Methods

<hr>

### project_create(project_name, owner_username=None):

Create a new project with given project name. The parameters are:

- _project_name:_ The name of the project
- _owner_username:_ (Optional) The owner username for the project. This parameter is useful in-case project needs to be created under some organization.

<hr>

### runs_list()

List the runs on the selected project.

<hr>

### runs_start(\_command, isDirect, commitId, title, tier, publishApiEndpoint*)

Start a new run on the selected project. The parameters are:

- _command:_ The command to run as an array of strings where members of the array represent arguments
  of the command. E.g. `["main.py", "hi mom"]`
- _isDirect:_ (Optional) Whether or not this command should be passed directly to a shell.
- _commitId:_ (Optional) The commitId to launch from. If not provided, will launch from latest commit.
- _title:_ (Optional) A title for the run.
- _tier:_ (Optional) The hardware tier to use for the run. This is the human-readable name of the hardware tier, such as "Free", "Small", or "Medium". Will use project default tier if not provided.
- _publishApiEndpoint:_ (Optional) Whether or not to publish an API endpoint from the resulting output.

<hr>

### runs_start_blocking(\_command, isDirect, commitId, title, tier, publishApiEndpoint, poll_freq=5, max_poll_time=6000*)

Same as method `run_start` except make a blocking request that waits until job is finished.

- _command:_ The command to run as an array of strings where members of the array represent arguments
  of the command. E.g. `["main.py", "hi mom"]`
- _isDirect:_ (Optional) Whether or not this command should be passed directly to a shell.
- _commitId:_ (Optional) The commitId to launch from. If not provided, will launch from latest commit.
- _title:_ (Optional) A title for the run.
- _tier:_ (Optional) The hardware tier to use for the run. Will use project default tier if not provided.
- _publishApiEndpoint:_ (Optional) Whether or not to publish an API endpoint from the resulting output.
- _poll_freq:_ (Optional) Number of seconds in between polling of the Domino server for status of the task that is running.
- _max_poll_time:_ (Optional) Maximum number of seconds to wait for a task to complete. If this threshold is exceeded, an exception is raised.
- _retry_count:_ (Optional) Maximum number of retry to do while polling (in-case of transient http errors). If this threshold is exceeded, an exception is raised.

<hr>

### run_stop(\*runId, saveChanges=True):

Stop an existing run in the selected project. The parameters are:

- _runId:_ string that identifies the run
- _saveChanges:_ (Defaults to True) If false, run results will be discarded.

<hr>

### runs_stdout(\_runId*)

Get stdout emitted by a particular run. The parameters are:

- _runId:_ string that identifies the run

<hr>

### files_list(\_commitId, path*)

List the files in a folder in the Domino project. The parameters are:

- _commitId:_ The commitId to list files from.
- _path:_ (Defaults to "/") The path to list from.

<hr>

### files_upload(\_path, file*)

Upload a Python file object into the specified path inside the project. See `examples/upload_file.py` for an example. The parameters, both of which are required, are:

- _path:_ The path to save the file to. For example, `/README.md` will write to the root directory of the project while `/data/numbers.csv` will save the file to a subfolder named `data` (if the `data` folder does not yet exist, it will be created)
- _file:_ A Python file object. For example, `f = open("authors.txt","rb")`

<hr>

### blobs_get(\_key*)

Retrieve a file from the Domino server by blob key. The parameters are:

- **key:** The key of the file to fetch from the blob server.

<hr>

### app_publish(\_unpublishRunningApps=True*, _hardwareTierId=None_)

Publishes an app in the Domino project, or republish an existing app. The parameters are:

- _unpublishRunningApps:_ (Defaults to True) Will check for any active app instances in the current project and unpublish them before publishing.
- _hardwareTierId:_ (Optional) Will launch the app on the specified hardware tier. Only applies for Domino 3.4+.

<hr>

### app_unpublish()

Stops all running apps in the Domino project.

<hr>

### job_start(\_command*, _commit_id=None_, _hardware_tier_name=None_, _environment_id=None_, _on_demand_spark_cluster_properties=None_):

Starts a new Job (run) in the project

- _command (string):_ Command to execute in Job. Ex `domino.job_start(command="main.py arg1 arg2")`
- _commit_id (string):_ (Optional) The commitId to launch from. If not provided, will launch from latest commit.
- _hardware_tier_name (string):_ (Optional) The hardware tier NAME to launch job in. If not provided it will use the default hardware tier for the project
- _environment_id (string):_ (Optional) The environment id to launch job with. If not provided it will use the default environment for the project
- _on_demand_spark_cluster_properties (dict):_ (Optional) On demand spark cluster properties. Following properties
  can be provided in spark cluster

  ```
  {
      "computeEnvironmentId": "<Environment ID configured with spark>"
      "executorCount": "<Number of Executors in cluster>"
       (optional defaults to 1)
      "executorHardwareTierId": "<Hardware tier ID for Spark Executors>"
       (optional defaults to last used historically if available)
      "masterHardwareTierId":  "<Hardware tier ID for Spark master"
       (optional defaults to last used historically if available)
      "executorStorageMB": "<Executor's storage in MB>"
       (optional defaults to 0; 1GB is 1000MB Here)
  }
  ```

- _param compute_cluster_properties (dict):_ (Optional) The compute cluster properties definition contains parameters for
  launching any Domino supported compute cluster for a job. Use this to launch a job that uses a compute cluster instead of
  the deprecated `on_demand_spark_cluster_properties` field. If `on_demand_spark_cluster_properties` and `compute_cluster_properties`
  are both present, `on_demand_spark_cluster_properties` will be ignored. `compute_cluster_properties` contains the following fields:

      ```
      {
          "clusterType": <string, one of "Ray", "Spark", "Dask", "MPI">,
          "computeEnvironmentId": <string, The environment ID for the cluster's nodes>,
          "computeEnvironmentRevisionSpec": <one of "ActiveRevision", "LatestRevision",
          {"revisionId":"<environment_revision_id>"} (optional)>,
          "masterHardwareTierId": <string, the Hardware tier ID for the cluster's master node (required unless clusterType is MPI)>,
          "workerCount": <number, the total workers to spawn for the cluster>,
          "workerHardwareTierId": <string, The Hardware tier ID for the cluster workers>,
           "workerStorage": <{ "value": <number>, "unit": <one of "GiB", "MB"> },
           The disk storage size for the cluster's worker nodes (optional)>
           "maxWorkerCount": <number, The max number of workers allowed. When
           this configuration exists, autoscaling is enabled for the cluster and
           "workerCount" is interpreted as the min number of workers allowed in the cluster
           (optional)>
      }
      ```

- _external_volume_mounts (List[string]):_ (Optional) External volume mount ids to mount to run. If not provided will launch with no external volume mounts mounted.

<hr>

### job_stop(\_job_id*, _commit_results=True_):

Stops the Job (run) in the project

- _job_id (string):_ Job identifier
- _commit_results (boolean):_ Defaults to `True`, if `false` job results will not be committed

<hr>

### job_status(\_job_id*):

Gets the status of a Job

- _job_id (string):_ Job identifier

<hr>

### job_start_blocking(\_poll_freq=5*, _max_poll_time=6000_, \*\*kwargs):

Starts a job and polls until the job is finished. Additionally this method supports all the
parameter in `job_start` method

- _poll_freq:_ Poll frequency interval in seconds
- _max_poll_time:_ Max poll time in seconds

<hr>

## Airflow

The `python-domino` client comes bundled with an Operator for use with airflow as an extra.

When installing the client from PyPI, add the `airflow` flag to extras:

```
pip install "dominodatalab[airflow]"
```

Similarly, when installing the client from GitHub, use the following command:

```
pip install -e git+https://github.com/dominodatalab/python-domino.git@1.0.6#egg="dominodatalab[airflow]"
```

### DominoOperator

```
from domino.airflow import DominoOperator
```

Allows a user to schedule domino runs via airflow. Follows the same function signature as `domino.runs_start` with two extra arguments:

- `startup_delay: Optional[int] = 10` | Add a startup delay to your job, useful if you want to delay execution until after other work finishes.
- `include_setup_log: Optional[bool] = True` | Determine whether or not to publish the setup log of the job as the log prefix before `stdout`.

### DominoSparkOperator

```
from domino.airflow import DominoSparkOperator
```

Allows a user to schedule domino runs via the v4 api, which supports `onDemandSparkClusters`. Follows the same function signature as `domino.job_start`, with the addition of `startup_delay` from above.

## License

This library is made available under the Apache 2.0 License.
This is an open-source project of [Domino Data Lab](https://www.dominodatalab.com).
