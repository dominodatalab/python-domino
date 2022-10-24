= python-domino

This library provides bindings for the Domino APIs.  See this documentation for details about the APIs:

* https://docs.dominodatalab.com/en/latest/api_guide/8c929e/domino-public-apis/[Latest public Domino APIs]
* https://dominodatalab.github.io/api-docs/[Legacy APIs]

The latest released version of `python-domino` is `1.2.0`.

== Version compatibility matrix

The `python-domino` library is compatible with different versions of Domino:

[cols=",^"]
|===
| Domino Versions | python-domino

| 3.6.x or lower
| http://github.com/dominodatalab/python-domino/archive/0.3.5.zip[0.3.5]

| 4.1.0 or higher
| https://github.com/dominodatalab/python-domino/archive/1.0.0.zip[1.0.0] or higher
|===

== Install python-domino

Starting from version `1.0.6`, `python-domino` is available on PyPI as `dominodatalab`:

[source,shell]
----
pip install dominodatalab
----

If you are adding install instructions for `python-domino` to your https://support.dominodatalab.com/hc/en-us/articles/115000392643-Compute-Environment-Management[Domino Environment^] Dockerfile Instructions field, you must add `RUN` to the beginning:

[source,shell]
----
RUN pip install dominodatalab
----

To install a specific version of the library from PyPI, such as `1.0.6`:

[source,shell]
----
pip install dominodatalab==1.0.6
----

To install a specific version of the library from GitHub, such as `1.0.6`:

[source,shell]
----
pip install https://github.com/dominodatalab/python-domino/archive/1.0.6.zip
----

== Development

The current `python-domino` is based on Python 3.9, which is therefore recommended for development.
Pipenv is also recommended to manage the dependencies.

To install dependencies from `setup.py` for development:

[source,shell]
----
pipenv install -e ".[dev]"
----

Use the same process for Airflow and data:

[source,shell]
----
pipenv install -e ".[data]" ".[airflow]"
----

== Set up the connection

You can set up the connection by creating a new instance of `Domino`:

._class_ Domino(project, api_key=None, host=None, domino_token_file=None, auth_token=None)

.Parameters

* _project:_ A project identifier (in the form of owner_user_name/projectname)
* _api_key:_ (Optional) An API key to authenticate with. 
If not provided, the library expects to find one in the `DOMINO_USER_API_KEY` environment variable.
* _host:_ (Optional) A host URL. 
If not provided, the library expects to find one in the `DOMINO_API_HOST` environment variable.
* _domino_token_file:_ (Optional) Path to domino token file containing auth token. 
If not provided, the library expects to find one in the `DOMINO_TOKEN_FILE` environment variable.
* _auth_token:_ (Optional) Authentication token.

[NOTE]
====
* The authentication preference should always be given to the authentication token. 
If it's not passed, the path to domino token file takes precedence, otherwise the API key is used. 
If none of these three parameters are passed, then preference is given to the Domino token file from the corresponding environment variable, then to the API key from the corresponding environment variable.
* By default, the log level is set to `INFO`.
To set the log level to `DEBUG`, set the `DOMINO_LOG_LEVEL` environment variable to `DEBUG`.
* For testing purposes and issues with SSL certificates, set the environment variable `DOMINO_VERIFY_CERTIFICATE` to `false`. 
Be sure to unset this variable when not in use.
====

== Methods

=== Projects

See https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_projects_usage.py[`example_projects_usage.py`] for example code.

==== project_create(project_name, owner_username=None)

Create a new project with given project name.

* _project_name:_ The name of the project.
* _owner_username:_ (Optional) The owner username for the project. 
This parameter is useful when you need to create a project under an organization.

==== collaborators_get()

Get the list of collaborators on a project.

==== collaborators_add(username_or_email, message="")

Add collaborators to a project.

* _username_or_email:_ Name or email of the Domino user to add as collaborator to the current project.
* _message:_ Optional - Message related to the user's role or purpose to the project.

=== Project tags

Project tags are an easy way to add freeform metadata to a project. 
Tags help colleagues and consumers organize and find the Domino projects that interest them. 
Tags can be used to describe the subject explored by a project, the packages and libraries it uses, or the source of the data within.

See https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_projects_usage.py[`example_projects_usage.py`] for example code.

==== tags_list(*project_id)

List a project's tags.

* _project_id:_ The project identifier.

==== tag_details(tag_id)

Get details about a tag.

* _tag_id:_ The tag identifier.

==== tags_add(tags, *project_id)

Create a tag, if it does not exist, and add it to a project.

* _tags (list):_ One or more tag names.

* _project_id:_ (Defaults to current project ID) The project identifier.

==== tag_get_id(tag_name, *project_id)

Get the tag ID using the tag string name.

* _tag_name (string):_ The tag name.
* _project_id:_ (Defaults to current project id) The project ID.

==== tags_remove(tag_name, project_id=None)

Remove a tag from a project.

* _tag_name (string):_ The tag name.
* _project_id:_ (Defaults to current project id) The project ID.

=== Executions

See these code example files:

* https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/start_run_and_check_status.py[`start_run_and_check_status.py`^]
* https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/export_runs.py[`export_runs.py`^]

==== runs_list()

List the executions on the selected project.

==== runs_start(command, isDirect, commitId, title, tier, publishApiEndpoint)

Start a new execution on the selected project. 

* _command:_ The command to execution as an array of strings where members of the array represent arguments of the command. 
For example: `["main.py", "hi mom"]`
* _isDirect:_ (Optional) Whether this command should be passed directly to a shell.
* _commitId:_ (Optional) The `commitId` to launch from. 
If not provided, the project launches from the latest commit.
* _title:_ (Optional) A title for the execution.
* _tier:_ (Optional) The hardware tier to use for the execution. 
This is the human-readable name of the hardware tier, such as "Free", "Small", or "Medium". 
If not provided, the project's default tier is used.
* _publishApiEndpoint:_ (Optional) Whether to publish an API endpoint from the resulting output.

==== runs_start_blocking(command, isDirect, commitId, title, tier, publishApiEndpoint, poll_freq=5, max_poll_time=6000)

Start a new execution on the selected project and make a blocking request that waits until job is finished.

* _command:_ The command to execution as an array of strings where members of the array represent arguments of the command. 
For example: `["main.py", "hi mom"]`
* _isDirect:_ (Optional) Whether this command should be passed directly to a shell.
* _commitId:_ (Optional) The `commitId` to launch from.
If not provided, the project launches from the latest commit.
* _title:_ (Optional) A title for the execution.
* _tier:_ (Optional) The hardware tier to use for the execution. 
Will use project's default tier if not provided.
If not provided, the project's default tier is used.
* _publishApiEndpoint:_ (Optional) Whether to publish an API endpoint from the resulting output.
* _poll_freq:_ (Optional) Number of seconds between polling of the Domino server for status of the task that is running.
* _max_poll_time:_ (Optional) Maximum number of seconds to wait for a task to complete. 
If this threshold is exceeded, an exception is raised.
* _retry_count:_ (Optional) Maximum number of polling retries (in case of transient HTTP errors). 
If this threshold is exceeded, an exception is raised.

==== run_stop(runId, saveChanges=True):

Stop an existing execution in the selected project.

* _runId:_ String that identifies the execution.
* _saveChanges:_ (Defaults to True) If false, execution results are discarded.

==== runs_stdout(runId)

Get `stdout` emitted by a particular execution.

* _runId:_ string that identifies the execution

=== Files and blobs

See these code example files:

* https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/upload_file.py[`upload_file.py`^]
* https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/upload_and_run_file_and_download_results.py[`upload_and_run_file_and_download_results.py`^]

==== files_list(commitId, path)

List the files in a folder in the Domino project.

* _commitId:_ The `commitId` to list files from.
* _path:_ (Defaults to "/") The path to list from.

==== files_upload(path, file)

Upload a Python file object into the specified path inside the project. 
See `examples/upload_file.py` for an example.
All parameters are required.

* _path:_ The path to save the file to. 
For example, `/README.md` writes to the root directory of the project while `/data/numbers.csv` saves the file to a sub folder named `data`.
If the specified folder does not yet exist, it is created.
* _file:_ A Python file object. 
For example: `f = open("authors.txt","rb")`

==== blobs_get(key)

Retrieve a file from the Domino server by blob key.

* _key:_ The key of the file to fetch from the blob server.

=== Apps

==== app_publish(unpublishRunningApps=True, hardwareTierId=None)

Publish an app in the Domino project, or republish an existing app. 

* _unpublishRunningApps:_ (Defaults to True) Check for active app instances in the current project and unpublish them before publishing.
* _hardwareTierId:_ (Optional) Launch the app on the specified hardware tier.

==== app_unpublish()

Stop all running apps in the Domino project.

=== Jobs

==== job_start(command, commit_id=None, hardware_tier_name=None, environment_id=None, on_demand_spark_cluster_properties=None):

Start a new job (execution) in the project.

* _command (string):_ Command to execute in Job. 
For example: `domino.job_start(command="main.py arg1 arg2")`
* _commit_id (string):_ (Optional) The `commitId` to launch from. 
If not provided, the job launches from the latest commit.
* _hardware_tier_name (string):_ (Optional) The hardware tier NAME to launch job in. 
If not provided, the project's default tier is used.
* _environment_id (string):_ (Optional) The environment ID with which to launch the job. 
If not provided, the project's default environment is used.
* _on_demand_spark_cluster_properties (dict):_ (Optional) On demand spark cluster properties. 
The following properties can be provided in the Spark cluster:
+
----
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
----

* _param compute_cluster_properties (dict):_ (Optional) The compute-cluster properties definition contains parameters for
launching any Domino supported compute cluster for a job. 
Use this to launch a job that uses a compute-cluster instead of the deprecated `on_demand_spark_cluster_properties` field.
If `on_demand_spark_cluster_properties` and `compute_cluster_properties` are both present, `on_demand_spark_cluster_properties` is ignored. `compute_cluster_properties` contains the following fields:
+
----
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
----

* _external_volume_mounts (List[string]):_ (Optional) External volume mount IDs to mount to execution. 
If not provided, the job launches with no external volumes mounted.

==== job_stop(job_id, commit_results=True):

Stop the Job (execution) in the project.

* _job_id (string):_ Job identifier.
* _commit_results (boolean):_ (Defaults to `true`) If `false`, the job results are not committed.

==== job_status(job_id):

Get the status of a job.

* _job_id (string):_ Job identifier.

==== job_start_blocking(poll_freq=5, max_poll_time=6000, **kwargs):

Start a job and poll until the job is finished. 
Additionally, this method supports all the parameters in the `job_start` method.

* _poll_freq:_ Poll frequency interval in seconds.
* _max_poll_time:_ Max poll time in seconds.

=== Datasets

A Domino dataset is a collection of files that are available in user executions as a filesystem directory.
A dataset always reflects the most recent version of the data.
You can modify the contents of a dataset through the Domino UI or through workload executions.

See https://docs.dominodatalab.com/en/latest/user_guide/0a8d11/datasets-overview/[Domino Datasets] for more details, and https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_dataset.py[`example_dataset.py`^] for example code.

==== datasets_list(project_id=None)

Provide a JSON list of all the available datasets.

* _project_id (string):_ (Defaults to None) The project identifier.
Each project can hold up to 5 datasets.

==== datasets_ids(project_id)

List the IDs the datasets for a particular project.

* _project_id:_ The project identifier.

==== datasets_names(project_id)

List the names the datasets for a particular project.

* _project_id:_ The project identifier.

==== datasets_details(dataset_id)

Provide details about a dataset.

* _dataset_id:_ The dataset identifier.

==== datasets_create(dataset_name, dataset_description)

Create a new dataset.

* _dataset_name:_ Name of the new dataset.
NOTE: The name must be unique.
* _dataset_description:_ Description of the dataset.

==== datasets_update_details(dataset_id, dataset_name=None, dataset_description=None)

Update a dataset's name or description.

* _dataset_id:_ The dataset identifier.
* _dataset_name:_ (Optional) New name of the dataset.
* _dataset_description:_ (Optional) New description of the dataset.

==== datasets_remove(dataset_ids)

Delete a set of datasets.

* _dataset_ids (list[string]):_ List of IDs of the datasets to delete.
NOTE: Datasets are first marked for deletion, then deleted after a grace period (15 minutes, configurable).
A Domino admin may also need to complete this process before the name can be reused.


== Airflow

The `python-domino` client comes bundled with an https://airflow.apache.org/docs/apache-airflow/stable/concepts/operators.html[Operator^] for use with https://airflow.apache.org/[Apache Airflow^] as an extra.

When installing the client from PyPI, add the `airflow` flag to extras:

[source,shell]
----
pip install "dominodatalab[airflow]"
----

Similarly, when installing the client from GitHub, use the following command:

[source,shell]
----
pip install -e git+https://github.com/dominodatalab/python-domino.git@1.0.6#egg="dominodatalab[airflow]"
----

See also https://github.com/dominodatalab/python-domino/blob/release-1.1.0/examples/example_airflow_dag.py[example_airflow_dag.py] for example code.

=== DominoOperator

[source,python]
----
from domino.airflow import DominoOperator
----

Allows a user to schedule Domino executions via Airflow. 
Follows the same function signature as `domino.runs_start` with two extra arguments:

[cols=2*]
|===
| `startup_delay: Optional[int] = 10`
| Add a startup delay to your job, useful if you want to delay execution until after other work finishes.
| `include_setup_log: Optional[bool] = True`
| Determine whether to publish the setup log of the job as the log prefix before `stdout`.
|===

=== DominoSparkOperator

[source,python]
----
from domino.airflow import DominoSparkOperator
----

Allows a user to schedule Domino executions via the v4 API, which supports `onDemandSparkClusters`. 
Follows the same function signature as `domino.job_start`, with the addition of `startup_delay` from above.

== License

This library is made available under the Apache 2.0 License.
This is an open-source project of https://www.dominodatalab.com[Domino Data Lab].
