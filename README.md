This library provides bindings for the Domino APIs. See this
documentation for details about the APIs:

-   [Latest public Domino
    APIs](https://docs.dominodatalab.com/en/latest/api_guide/8c929e/domino-public-apis/)

-   [Legacy APIs](https://dominodatalab.github.io/api-docs/)

The latest released version of `python-domino` is `1.2.1`.

# Version compatibility matrix

The `python-domino` library is compatible with different versions of
Domino:

| Domino Versions |                                    Python-Domino                                    |
|-----------------|:-----------------------------------------------------------------------------------:|
| 3.6.x or lower  |      [0.3.5](http://github.com/dominodatalab/python-domino/archive/0.3.5.zip)       |
| 4.1.0 or higher | [1.0.0](https://github.com/dominodatalab/python-domino/archive/1.0.0.zip) or Higher |
| 5.3.0 or higher | [1.2.0](https://github.com/dominodatalab/python-domino/archive/1.2.0.zip) or Higher |

# Install python-domino

Starting from version `1.0.6`, `python-domino` is available on PyPI as `dominodatalab`:

    pip install dominodatalab

If you are adding install instructions for `python-domino` to your [Domino Environment](https://support.dominodatalab.com/hc/en-us/articles/115000392643-Compute-Environment-Management) Dockerfile Instructions field, you must add `RUN` to the beginning:

    RUN pip install dominodatalab

To install a specific version of the library from PyPI, such as `1.0.6`:

    pip install dominodatalab==1.0.6

To install a specific version of the library from GitHub, such as
`1.0.6`:

    pip install https://github.com/dominodatalab/python-domino/archive/1.0.6.zip

# Development

The current `python-domino` is based on Python 3.9, which is therefore recommended for development. Pipenv is also recommended to manage the dependencies.

To install dependencies from `setup.py` for development:

    pipenv install -e ".[dev]"

Use the same process for Airflow and data:

    pipenv install -e ".[data]" ".[airflow]"

# Set up the connection

You can set up the connection by creating a new instance of `Domino`:

-   *project:* A project identifier (in the form of
    ownerusername/projectname).
    
-   *api_proxy:* (Optional) Location of the Domino API reverse proxy as host:port.
    If set, this proxy will be used to intercept any Domino API requests and insert an auth token.
    This is the preferred method of authentication. Alternatively, the same behavior can be achieved
    by setting the `DOMINO_API_PROXY` environment variable (this variable is set inside a Domino run
    container in version 5.4.0 or later). Note this mechanism will not work when connecting to a
    HTTPS endpoint, so it is mainly meant to be used inside Domino runs.

-   *api_key:* (Optional) An API key to authenticate with. If not
    provided, the library expects to find one in the
    `DOMINO_USER_API_KEY` environment variable.

-   *host:* (Optional) A host URL. If not provided, the library expects
    to find one in the `DOMINO_API_HOST` environment variable.

-   *domino_token_file:* (Optional) Path to domino token file
    containing auth token. If not provided, the library expects to find
    one in the `DOMINO_TOKEN_FILE` environment variable.

-   *auth_token:* (Optional) Authentication token.

-   The authentication preference should be given to the API proxy.
    If it’s not passed, then the authentication token takes precedence, then the path to the domino
    token file, otherwise the API key is used. If none of
    these four parameters are passed, then preference is given to the Api Proxy from the
    corresponding environment variable, then the Domino token file from the corresponding
    environment variable, then to the API key from the corresponding environment variable.

-   By default, the log level is set to `INFO`. To set the log level to
    `DEBUG`, set the `DOMINO_LOG_LEVEL` environment variable to `DEBUG`.

-   For testing purposes and issues with SSL certificates, set the
    environment variable `DOMINO_VERIFY_CERTIFICATE` to `false`. Be sure
    to unset this variable when not in use.

# Methods

## Projects

See
[`example_projects_usage.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_projects_usage.py)
for example code.

### project_create(project_name, owner_username=None)

Create a new project with given project name.

-   *project_name:* The name of the project.

-   *owner_username:* (Optional) The owner username for the project.
    This parameter is useful when you need to create a project under an
    organization.

### collaborators_get()

Get the list of collaborators on a project.

### collaborators_add(username_or_email, message="")

Add collaborators to a project.

-   *username_or_email:* Name or email of the Domino user to add as
    collaborator to the current project.

-   *message:* Optional - Message related to the user’s role or purpose
    to the project.

## Project tags

Project tags are an easy way to add freeform metadata to a project. Tags
help colleagues and consumers organize and find the Domino projects that
interest them. Tags can be used to describe the subject explored by a
project, the packages and libraries it uses, or the source of the data
within.

See
[`example_projects_usage.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_projects_usage.py)
for example code.

### tags_list(\*project_id)

List a project’s tags.

-   *project_id:* The project identifier.

### tag_details(tag_id)

Get details about a tag.

-   *tag_id:* The tag identifier.

### tags_add(tags, \*project_id)

Create a tag, if it does not exist, and add it to a project.

-   *tags (list):* One or more tag names.

-   *project_id:* (Defaults to current project ID) The project
    identifier.

### tag_get_id(tag_name, \*project_id)

Get the tag ID using the tag string name.

-   *tag_name (string):* The tag name.

-   *project_id:* (Defaults to current project id) The project ID.

### tags_remove(tag_name, project_id=None)

Remove a tag from a project.

-   *tag_name (string):* The tag name.

-   *project_id:* (Defaults to current project id) The project ID.

## Executions

See these code example files:

-   [`start_run_and_check_status.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/start_run_and_check_status.py)

-   [`export_runs.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/export_runs.py)

### runs_list()

List the executions on the selected project.

### runs_start(command, isDirect, commitId, title, tier, publishApiEndpoint)

Start a new execution on the selected project.

-   *command:* The command to execution as an array of strings where
    members of the array represent arguments of the command. For
    example: `["main.py", "hi mom"]`

-   *isDirect:* (Optional) Whether this command should be passed
    directly to a shell.

-   *commitId:* (Optional) The `commitId` to launch from. If not
    provided, the project launches from the latest commit.

-   *title:* (Optional) A title for the execution.

-   *tier:* (Optional) The hardware tier to use for the execution. This
    is the human-readable name of the hardware tier, such as "Free",
    "Small", or "Medium". If not provided, the project’s default tier is
    used.

-   *publishApiEndpoint:* (Optional) Whether to publish an API endpoint
    from the resulting output.

### runs_start_blocking(command, isDirect, commitId, title, tier, publishApiEndpoint, poll_freq=5, max_poll_time=6000)

Start a new execution on the selected project and make a blocking
request that waits until job is finished.

-   *command:* The command to execution as an array of strings where
    members of the array represent arguments of the command. For
    example: `["main.py", "hi mom"]`

-   *isDirect:* (Optional) Whether this command should be passed
    directly to a shell.

-   *commitId:* (Optional) The `commitId` to launch from. If not
    provided, the project launches from the latest commit.

-   *title:* (Optional) A title for the execution.

-   *tier:* (Optional) The hardware tier to use for the execution. Will
    use project’s default tier if not provided. If not provided, the
    project’s default tier is used.

-   *publishApiEndpoint:* (Optional) Whether to publish an API endpoint
    from the resulting output.

-   *poll_freq:* (Optional) Number of seconds between polling of the
    Domino server for status of the task that is running.

-   *max_poll_time:* (Optional) Maximum number of seconds to wait for
    a task to complete. If this threshold is exceeded, an exception is
    raised.

-   *retry_count:* (Optional) Maximum number of polling retries (in
    case of transient HTTP errors). If this threshold is exceeded, an
    exception is raised.

### run_stop(runId, saveChanges=True):

Stop an existing execution in the selected project.

-   *runId:* String that identifies the execution.

-   *saveChanges:* (Defaults to True) If false, execution results are
    discarded.

### runs_stdout(runId)

Get `stdout` emitted by a particular execution.

-   *runId:* string that identifies the execution

## Files and blobs

See these code example files:

-   [`upload_file.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/upload_file.py)

-   [`upload_and_run_file_and_download_results.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/upload_and_run_file_and_download_results.py)

### files_list(commitId, path)

List the files in a folder in the Domino project.

-   *commitId:* The `commitId` to list files from.

-   *path:* (Defaults to "/") The path to list from.

### files_upload(path, file)

Upload a Python file object into the specified path inside the project.
See `examples/upload_file.py` for an example. All parameters are
required.

-   *path:* The path to save the file to. For example, `/README.md`
    writes to the root directory of the project while
    `/data/numbers.csv` saves the file to a sub folder named `data`. If
    the specified folder does not yet exist, it is created.

-   *file:* A Python file object. For example:
    `f = open("authors.txt","rb")`

### blobs_get(key)

Retrieve a file from the Domino server by blob key.

-   *key:* The key of the file to fetch from the blob server.

## Apps

### app_publish(unpublishRunningApps=True, hardwareTierId=None)

Publish an app in the Domino project, or republish an existing app.

-   *unpublishRunningApps:* (Defaults to True) Check for active app
    instances in the current project and unpublish them before
    publishing.

-   *hardwareTierId:* (Optional) Launch the app on the specified
    hardware tier.

### app_unpublish()

Stop all running apps in the Domino project.

## Jobs

### job_start(command, commit_id=None, hardware_tier_name=None, environment_id=None, on_demand_spark_cluster_properties=None):

Start a new job (execution) in the project.

-   *command (string):* Command to execute in Job. For example:
    `domino.job_start(command="main.py arg1 arg2")`

-   *commit_id (string):* (Optional) The `commitId` to launch from. If
    not provided, the job launches from the latest commit.

-   *hardware_tier_name (string):* (Optional) The hardware tier NAME
    to launch job in. If not provided, the project’s default tier is
    used.

-   *environment_id (string):* (Optional) The environment ID with which
    to launch the job. If not provided, the project’s default
    environment is used.

-   *on_demand_spark_cluster_properties (dict):* (Optional) On
    demand spark cluster properties. The following properties can be
    provided in the Spark cluster:

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

-   *param compute_cluster_properties (dict):* (Optional) The
    compute-cluster properties definition contains parameters for
    launching any Domino supported compute cluster for a job. Use this
    to launch a job that uses a compute-cluster instead of the
    deprecated `on_demand_spark_cluster_properties` field. If
    `on_demand_spark_cluster_properties` and
    `compute_cluster_properties` are both present,
    `on_demand_spark_cluster_properties` is ignored.
    `compute_cluster_properties` contains the following fields:

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

-   *external_volume_mounts (List\[string\]):* (Optional) External
    volume mount IDs to mount to execution. If not provided, the job
    launches with no external volumes mounted.

### job_stop(job_id, commit_results=True):

Stop the Job (execution) in the project.

-   *job_id (string):* Job identifier.

-   *commit_results (boolean):* (Defaults to `true`) If `false`, the
    job results are not committed.

### job_status(job_id):

Get the status of a job.

-   *job_id (string):* Job identifier.

### job_start_blocking(poll_freq=5, max_poll_time=6000, \*\*kwargs):

Start a job and poll until the job is finished. Additionally, this
method supports all the parameters in the `job_start` method.

-   *poll_freq:* Poll frequency interval in seconds.

-   *max_poll_time:* Max poll time in seconds.

## Datasets

A Domino dataset is a collection of files that are available in user
executions as a filesystem directory. A dataset always reflects the most
recent version of the data. You can modify the contents of a dataset
through the Domino UI or through workload executions.

See [Domino
Datasets](https://docs.dominodatalab.com/en/latest/user_guide/0a8d11/datasets-overview/)
for more details, and
[`example_dataset.py`](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_dataset.py)
for example code.

### datasets_list(project_id=None)

Provide a JSON list of all the available datasets.

-   *project_id (string):* (Defaults to None) The project identifier.
    Each project can hold up to 5 datasets.

### datasets_ids(project_id)

List the IDs the datasets for a particular project.

-   *project_id:* The project identifier.

### datasets_names(project_id)

List the names the datasets for a particular project.

-   *project_id:* The project identifier.

### datasets_details(dataset_id)

Provide details about a dataset.

-   *dataset_id:* The dataset identifier.

### datasets_create(dataset_name, dataset_description)

Create a new dataset.

-   *dataset_name:* Name of the new dataset. NOTE: The name must be
    unique.

-   *dataset_description:* Description of the dataset.

### datasets_update_details(dataset_id, dataset_name=None, dataset_description=None)

Update a dataset’s name or description.

-   *dataset_id:* The dataset identifier.

-   *dataset_name:* (Optional) New name of the dataset.

-   *dataset_description:* (Optional) New description of the dataset.

### datasets_remove(dataset_ids)

Delete a set of datasets.

-   *dataset_ids (list\[string\]):* List of IDs of the datasets to
    delete. NOTE: Datasets are first marked for deletion, then deleted
    after a grace period (15 minutes, configurable). A Domino admin may
    also need to complete this process before the name can be reused.

# Airflow

The `python-domino` client comes bundled with an
[Operator](https://airflow.apache.org/docs/apache-airflow/stable/concepts/operators.html)
for use with [Apache Airflow](https://airflow.apache.org/) as an extra.

When installing the client from PyPI, add the `airflow` flag to extras:

    pip install "dominodatalab[airflow]"

Similarly, when installing the client from GitHub, use the following
command:

    pip install -e git+https://github.com/dominodatalab/python-domino.git@1.0.6#egg="dominodatalab[airflow]"

See also
[example_airflow_dag.py](https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_airflow_dag.py)
for example code.

## DominoOperator

    from domino.airflow import DominoOperator

Allows a user to schedule Domino executions via Airflow. Follows the
same function signature as `domino.runs_start` with two extra arguments:

- `startup_delay: Optional[int] = 10` | Add a startup delay to your job, useful if you want to delay execution until after other work finishes.
- `include_setup_log: Optional[bool] = True` | Determine whether or not to publish the setup log of the job as the log prefix before `stdout`.

## DominoSparkOperator

    from domino.airflow import DominoSparkOperator

Allows a user to schedule Domino executions via the v4 API, which
supports `onDemandSparkClusters`. Follows the same function signature as
`domino.job_start`, with the addition of `startup_delay` from above.

# License

This library is made available under the Apache 2.0 License. This is an
open-source project of [Domino Data Lab](https://www.dominodatalab.com).
