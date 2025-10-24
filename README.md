This library provides bindings for the Domino APIs.  It ships with the Domino Standard Environment (DSE).

See this documentation for details about the APIs:

-   [Latest public Domino
    APIs](https://docs.dominodatalab.com/en/latest/api_guide/8c929e/domino-public-apis/)

-   [Legacy APIs](https://dominodatalab.github.io/api-docs/)

The latest released version of `python-domino` is `1.5.1`.

# Version compatibility matrix

The `python-domino` library is compatible with different versions of
Domino:

| Domino Versions |                                             Python-Domino                                             |
|-----------------|:-----------------------------------------------------------------------------------------------------:|
| 3.6.x or lower  |               [0.3.5](https://github.com/dominodatalab/python-domino/archive/0.3.5.zip)               |
| 4.1.0 or higher |     [1.0.0](https://github.com/dominodatalab/python-domino/archive/refs/tags/1.0.0.zip) or Higher     |
| 5.3.0 or higher | [1.2.0](https://github.com/dominodatalab/python-domino/archive/refs/tags/Release-1.2.0.zip) or Higher |
| 5.5.0 or higher | [1.2.2](https://github.com/dominodatalab/python-domino/archive/refs/tags/Release-1.2.2.zip) or Higher |
| 5.10.0 or higher | [1.3.1](https://github.com/dominodatalab/python-domino/archive/refs/tags/Release-1.3.1.zip) or Higher |
| 5.11.0 or higher | [1.4.1](https://github.com/dominodatalab/python-domino/archive/refs/tags/Release-1.4.1.zip) or Higher |
| 6.0.0 or higher | [1.4.8](https://github.com/dominodatalab/python-domino/archive/refs/tags/Release-1.4.8.zip) or Higher |
| 6.2.0 or higher | [1.5.1](https://github.com/dominodatalab/python-domino/archive/refs/tags/Release-1.5.1.zip) or Higher |

# Development

The current `python-domino` is based on Python 3.10, which is therefore recommended for development. `Pipenv` is also recommended to manage the dependencies.

To use the Python binding in a Domino workbook session, include `dominodatalab` in your project's requirements.txt file.
This makes the Python binding available for each new workbook session (or batch run) started within the project.

To install dependencies from `setup.py` for development:

    pipenv --python 3.10 install -e ".[dev]"

Use the same process for Airflow, aisystems, and data:

    pipenv --python 3.10 install -e ".[data]" ".[airflow]" ".[aisystems]"

# Set up the connection

You can set up the connection by creating a new instance of `Domino`:

    _class_ Domino(project, api_key=None, host=None, domino_token_file=None, auth_token=None)

-   *project:* A project identifier (in the form of ownerusername/projectname).
    
-   *api_proxy:* (Optional) Location of the Domino API reverse proxy as host:port.

    If set, this proxy is used to intercept any Domino API requests and insert an authentication token.
    _This is the preferred method of authentication_. 
    Alternatively, set the `DOMINO_API_PROXY` environment variable.
    In Domino 5.4.0 or later, this variable is set inside a Domino run container.

    NOTE: This mechanism does not work when connecting to an HTTPS endpoint; it is meant to be used inside Domino runs.

-   *api_key:* (Optional) An API key to authenticate with. 

    If not provided, the library expects to find one in the `DOMINO_USER_API_KEY` environment variable.
    If you are using the Python package in code that is already running in Domino, the `DOMINO_API_USER_KEY` variable is set automatically to be the key for the user who started the run.

-   *host:* (Optional) A host URL. 

    If not provided, the library expects to find one in the `DOMINO_API_HOST` environment variable.

-   *domino_token_file:* (Optional) Path to the Domino token file
    containing the auth token. 

    If not provided, the library expects to find one in the `DOMINO_TOKEN_FILE` environment variable.
    If you are using Python package in code that is already running in Domino, the `DOMINO_TOKEN_FILE` is set automatically to be the token file for the user who started the run.

-   *auth_token:* (Optional) Authentication token.

## Authentication

Domino looks for the authentication method in the following order and uses the first one it finds:

1. `api_proxy`
2. `auth_token`
3. `domino_token_file`
4. `api_key`
5. `DOMINO_API_PROXY`
6. `DOMINO_TOKEN_FILE`
7. `DOMINO_USER_API_KEY`

The API proxy is the preferred method of authentication.
See 
[Use the API Proxy to Authenticate Calls to the Domino API](https://docs.dominodatalab.com/en/latest/user_guide/40b91f/domino-api/).

## Additional environment variables

- `DOMINO_LOG_LEVEL`
  
    The default log level is `INFO`.
    You can change the log level by setting `DOMINO_LOG_LEVEL`, for example to `DEBUG`.

- `DOMINO_VERIFY_CERTIFICATE`
  
    For testing purposes and issues with SSL certificates, set `DOMINO_VERIFY_CERTIFICATE` to `false`. 
    Be sure to unset this variable when not in use.

- `DOMINO_MAX_RETRIES`
    
    Default Retry is set to 4 
    Determines the number of attempts for the request session in case of a ConnectionError
    Get more info on request max timeout/error durations based on Retry and backoff factors [here](https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry)

- `MLFLOW_TRACKING_URI`

    Must be set for the `domino.aisystems` package to work properly. This will be set automatically in executions, e.g. Jobs, Workspaces, Scheduled Jobs, etc.
    For testing, the value must be set on the command line to "http://localhost:5000".

- `DOMINO_AI_SYSTEM_CONFIG_PATH`

    Used by the `domino.aisystems` package. May be set to point to the location of the `ai_system_config.yaml`.

- `DOMINO_AI_SYSTEM_IS_PROD`

    Used by the `domino.aisystems` package. Indicates that an AI System is running in production or development mode.

# Working with docs

## building locally

- Install the app in dev mode and all dependencies and pandoc: `brew install pandoc ghc cabal-install haskell-stack` and `cabal update && cabal install --lib pandoc-types --package-env .`
- Build: `./docs/build.sh`
- View: open docs/build/html/index.html
- Manually pick the changes you want and add to `README.adoc` and `README.md`. Update the styling of the docs as needed.

## transform aisystems docs for README

- Run:
`./docs/transform_aisystems_docs_for_readme.sh`
- copy/paste the outputs for asciidoc and markdown into respective README files

# Methods

# Budgets and Billing Tags

See
[`example_budget_manager.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/example_budget_manager.py)
for example code.

### budget_defaults_list()

Get a list of the available default budgets with the assigned (if any) limits
Requires Admin permission

### budget_defaults_update(budget_label, budget_limit)

Update default budgets by BudgetLabel
Requires Admin roles

-   *budget_label:* (required) label of budget to be updated ex: `BillingTag`, `Organization`

-   *budget_limit:* (required) new budget quota to assign to default label

### budget_overrides_list()

Get a list of the available budgets overrides with the assigned limits.
Requires Admin permission

### budget_override_create(budget_label, budget_id, budget_limit)

Create Budget overrides based on BudgetLabels, ie BillingTags, Organization, or Projects
the object id is used as budget ids
Requires Admin roles

-   *budget_label:* label of budget to be updated

-   *budget_id:* id of project or organization to be used as new budget override id.

-   *budget_limit:* budget quota to assign to override

### budget_override_update(budget_label, budget_id, budget_limit)

Update Budget overrides based on BudgetLabel and budget id
Requires Admin roles

-   *budget_label:* label of budget to be updated

-   *budget_id:* id of budget override to be updated.

-   *budget_limit:* new budget quota to assign to override

### budget_override_delete(budget_id)

Delete an existing budget override
Requires Admin roles

-   *budget_id:* id of budget override to be deleted.

### budget_alerts_settings()

Get the current budget alerts settings
Requires Admin permission

### budget_alerts_settings_update(alerts_enabled, notify_org_owner)

Update the current budget alerts settings to enable/disable budget notifications
and whether to notify org owners on projects notifications
Requires Admin permission

-   *alerts_enabled:* whether to enable or disable notifications.

-   *notify_org_owner:* whether to notify organizations owners on projects reaching threshold.

### budget_alerts_targets_update(targets)

Update the current budget alerts settings with additional email targets per budget label
Requires Admin permission

-   *targets:* dictionary of budget labels and list of email addresses

### billing_tags_list_active()

Get a list of active billing tags
Requires Admin permission

### billing_tags_create(tags_list)

Create a list of active billing tags
Requires Admin permission

-   *tags_list:* list of billing tags names to be created

### active_billing_tag_by_name(name)

Get detailed info on active or archived billing tag
Requires Admin permission

-   *name:* name of existing billing tag

### billing_tag_archive(name)

Archive an active billing tag
Requires Admin permission

-   *name:* name of existing billing tag to archive

### billing_tag_settings()

Get the current billing tag settings
Requires Admin permission

### billing_tag_settings_mode()

Get the current billing tag settings mode
Requires Admin permission

### billing_tag_settings_mode_update(mode)

Update the current billing tag settings mode
Requires Admin permission

-   *mode:* new mode to set the billing tag settings (see BillingTagSettingMode)

### project_billing_tag(project_id)

Get a billing tag assigned to a particular project by project id
Requires Admin permission

-   *project_id:* id of the project to find assigned billing tag

###  project_billing_tag_update(billing_tag, project_id)

Update project's billing tag with new billing tag.
Requires Admin permission

-   *billing_tag:* billing tag to assign to a project

-   *project_id:* id of the project to assign a billing tag

### project_billing_tag_reset(project_id)

Remove a billing tag from a specified project
Requires Admin permission

-   *project_id:* id of the project to reset billing tag field

### projects_by_billing_tag( billing_tag, offset, page_size, name_filter, sort_by, sort_order, missing_tag_only=False)

Remove a billing tag from a specified project
Requires Admin permission

-   *billing_tag:* billing tag string to filter projects by

-   *offset:* The index of the start of the page, where checkpointProjectId is index 0.
If the offset is negative the project it points to will be the end of the page.
-   *page_size:* The number of records to return per page.

-   *name_filter:* matches projects by name substring

-   *sort_by:* (Optional) field to sort the projects on

-   *sort_order:* (Optional) Whether to sort in asc or desc order

-   *missing_tag_only:* (Optional) determine whether to only return projects with missing tag

### project_billing_tag_bulk_update(projects_tag)

Update project's billing tags in bulk
Requires Admin permission

-   *projects_tag:* dictionary of project_id and billing_tags


## Projects

See
[`example_projects_usage.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/example_projects_usage.py)
for example code.

### project_create_v4(project_name, owner_id, owner_username, description, collaborators, tags, billing_tag, visibility=PUBLIC)

Newer version of projects creation using the v4 endpoints which allows more optional fields.

-   *project_name:* (required) The name of the project.

-   *owner_id:* (Optional) user id of the owner of the new project to be created (must be admin to create projects for other users)
  owner_id or owner_username can be used, both are not needed (Defaults to current owner_username)

-   *owner_username:* (Optional) username of the owner of the new project to be created (must be admin to create projects for other users)
  owner_id or owner_username can be used, both are not needed (Defaults to current owner_username)

-   *description:* (Optional) description of the project

-   *collaborators:* (Optional) list of collaborators to be added to the project

-   *tags:* (Optional) list of tags to add to project

-   *billing_tag:* (Optional unless billingTag settings mode is Required) active billing tag to be added to projects for governance

-   *visibility:* (Optional) (Defaults to Public) project visibility 

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
[`example_projects_usage.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/example_projects_usage.py)
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

-   [`start_run_and_check_status.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/start_run_and_check_status.py)

-   [`export_runs.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/export_runs.py)

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

-   [`upload_file.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/upload_file.py)

-   [`upload_and_run_file_and_download_results.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/upload_and_run_file_and_download_results.py)

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

*_Deprecated_* Retrieve a file from the Domino server by blob key. Use blobs_get_v2(path, commit_id, project_id) instead.

-   *key:* The key of the file to fetch from the blob server.

### blobs_get_v2(path, commit_id, project_id)

Retrieve a file from the Domino server in a project from its path and commit id.

-   *path:* The path to the file in the Domino project.
-   *commit_id:* ID of the commit to retrieve the file from.
-   *project_id:* ID of the project to retrieve the file from.

## Apps

### app_publish(unpublishRunningApps=True, hardwareTierId=None)

Publish an app within a project, or republish an existing app.

-   *unpublishRunningApps:* (Defaults to True) Check for an active app
    instance in the current project and unpublish it before
    re/publishing.

-   *hardwareTierId:* (Optional) Launch the app on the specified
    hardware tier.

### app_unpublish()

Stop the running app in the project.

## Jobs

### job_start(command, commit_id=None, hardware_tier_name=None, environment_id=None, on_demand_spark_cluster_properties=None, compute_cluster_properties=None, external_volume_mounts=None, title=None):

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

-   *title (string): (Optional) Title for Job.

### job_stop(job_id, commit_results=True):

Stop the Job (execution) in the project.

-   *job_id (string):* Job identifier.

-   *commit_results (boolean):* (Defaults to `true`) If `false`, the
    job results are not committed.

### jobs_list(self, project_id: str, order_by: str = "number", sort_by: str = "desc", page_size: Optional[int] = None, page_no: int = 1, show_archived: str = "false", status: str = "all", tag: Optional[str] = None):

Lists job history for a given project_id

-   *project_id (string):* The project to query

-   *order_by (string):* Field on which sort has to be applied– e.g. "title" (default "number")

-   *sort_by (string):* Sort "desc" (default) or "asc"

-   *page_size (integer):* The number of jobs to return (default: 3)

-   *page_no (integer):* Page number to fetch (default: 1).

-   *show_archived (string):* Show archived jobs in results (default: false)

-   *status (string):* Status of jobs to fetch– e.g. "completed" (default: "all")

-   *tag (string):* Optional tag filter

### job_status(job_id):

Get the status of a job.

-   *job_id (string):* Job identifier.

### job_restart(job_id, should_use_original_input_commit=True):

Restart a previous job

-   *job_id (string):* ID of the original job. This can be obtained with `jobs_list()`.

-   *should_use_original_input_commit (bool):* Should the new job run use the original code, or the current version?

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
[`example_dataset.py`](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/example_dataset.py)
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

### datasets_upload_files(dataset_id, local_path_to_file_or_directory, file_upload_setting, max_workers, target_chunk_size, target_relative_path)

Uploads a file or entire directory to a dataset.

-   *dataset_id:* The dataset identifier.
-   *local_path_to_file_or_directory:* The path to the file or directory in local machine.
-   *file_upload_setting:* The setting to resolve naming conflict, must be one of `Overwrite`, `Rename`, `Ignore` (default).
-   *max_workers:* The max amount of threads (default: 10).
-   *target_chunk_size:* The max chunk size for multipart upload (default: 8MB).
-   *target_relative_path:* The path on the dataset to upload the file or directory to. Note that the path must exist or the upload will fail.
   
# AISystems 


## domino.aisystems.environment_variables

DOMINO_AI_SYSTEM_CONFIG_PATH:  
For configuring the location of the ai_system_config.yaml file. If not
set, defaults to ‘./ai_system_config.yaml’.

type:  
str

DOMINO_AI_SYSTEM_MODEL_ID:  
The ID of the production AI System

type:  
str

## domino.aisystems.logging

Functions

|  |  |
|----|----|
| `log_evaluation`(trace_id, name, value) | This logs evaluation data and metadata to a parent trace. |

Classes

|  |  |
|----|----|
| `DominoRun`(\[experiment_name, run_id, ...\]) | DominoRun is a context manager that starts an Mlflow run and attaches the user's AI System configuration to it, create a Logged Model with the AI System configuration, and computes summary metrics for evaluation traces made during the run. |

### *class* domino.aisystems.logging.DominoRun(*experiment_name: str \| None = None*, *run_id: str \| None = None*, *ai_system_config_path: str \| None = None*, *custom_summary_metrics: list\[str, Literal\['mean', 'median', 'stdev', 'max', 'min'\]\] \| None = None*)  
Bases: `object`

DominoRun is a context manager that starts an Mlflow run and attaches
the user’s AI System configuration to it, create a Logged Model with the
AI System configuration, and computes summary metrics for evaluation
traces made during the run. Average metrics are computed by default, but
the user can provide a custom list of evaluation metric aggregators.
This is intended to be used in development mode for AI System
evaluation. Context manager docs:
https://docs.python.org/3/library/contextlib.html

Parallelism: DominoRun is not thread-safe. Runs in different threads
will work correctly. This is due to Mlflow’s architecture. Parallelizing
operations within a single DominoRun context however, is supported.

Example

import mlflow

mlflow.set_experiment(“my_experiment”)

with DominoRun():  
train_model()

Parameters:  
- **experiment_name** – the name of the mlflow experiment to log the run
  to.

- **run_id** – optional, the ID of the mlflow run to continue logging
  to. If not provided a new run will start.

- **ai_system_config_path** – the optional path to the AI System
  configuration file. If not provided, defaults to the
  DOMINO_AI_SYSTEM_CONFIG_PATH environment variable.

- **custom_summary_metrics** – an optional list of tuples that define
  what summary statistic to use with what evaluation metric.

- **are** (*Valid summary statistics*) – “mean”, “median”, “stdev”,
  “max”, “min” e.g. \[(“hallucination_rate”, “max”)\]

Returns: DominoRun context manager

&nbsp;

### domino.aisystems.logging.log_evaluation(*trace_id: str*, *name: str*, *value: float \| str*)  
This logs evaluation data and metadata to a parent trace. This is used
to log the evaluation of a span after it was created. This is useful for
analyzing past performance of an AI System component.

Parameters:  
- **trace_id** – the ID of the trace to evaluate

- **name** – a label for the evaluation result. This is used to identify
  the evaluation result

- **value** – the evaluation result to log. This must be a float or
  string

Modules

|             |     |
|-------------|-----|
| `dominorun` |     |
| `logging`   |     |

## domino.aisystems.tracing

Functions

|  |  |
|----|----|
| `add_tracing`(name\[, autolog_frameworks, ...\]) | This is a decorator that starts an mlflow span for the function it decorates. |
| `init_tracing`(\[autolog_frameworks\]) | Initialize Mlflow autologging for various frameworks and sets the active experiment to enable tracing in production. |
| `search_ai_system_traces`(ai_system_id\[, ...\]) | This allows searching for traces that have a certain name and returns a paginated response of trace summaries that include the spans that were requested. |
| `search_traces`(run_id\[, trace_name, ...\]) | This allows searching for traces that have a certain name and returns a paginated response of trace summaries that inclued the spans that were requested. |

Classes

|  |  |
|----|----|
| `SearchTracesResponse`(data, page_token) | The response from searching for traces. |
| `SpanSummary`(id, name, trace_id, inputs, outputs) | A span in a trace. |
| `TraceSummary`(name, id, spans, evaluation_results) | A summary of a trace. |

### *class* domino.aisystems.tracing.SearchTracesResponse(*data: list\[TraceSummary\]*, *page_token: str \| None*)  
Bases: `object`

The response from searching for traces.

data*: list\[TraceSummary\]*  
The list of trace summaries

page_token*: str \| None*  
The token for the next page of results

&nbsp;

### *class* domino.aisystems.tracing.SpanSummary(*id: str*, *name: str*, *trace_id: str*, *inputs: Any*, *outputs: Any*)  
Bases: `object`

A span in a trace.

id*: str*  
the mlflow ID of the span

inputs*: Any*  
The inputs to the function that created the span

name*: str*  
The name of the span

outputs*: Any*  
The outputs of the function that created the span

trace_id*: str*  
The parent trace ID

&nbsp;

### *class* domino.aisystems.tracing.TraceSummary(*name: str*, *id: str*, *spans: list\[SpanSummary\]*, *evaluation_results: list\[EvaluationResult\]*)  
Bases: `object`

A summary of a trace.

evaluation_results*: list\[EvaluationResult\]*  
The evaluation results for this trace

id*: str*  
The mlflow ID of the trace

name*: str*  
The name of the trace

spans*: list\[SpanSummary\]*  
The child spans of this trace

&nbsp;

### domino.aisystems.tracing.add_tracing(*name: str*, *autolog_frameworks: list\[str\] \| None = \[\]*, *evaluator: Callable\[\[mlflow.entities.Span\], dict\[str, int \| float \| str\]\] \| None = None*, *trace_evaluator: Callable\[\[mlflow.entities.Trace\], dict\[str, int \| float \| str\]\] \| None = None*, *eagerly_evaluate_streamed_results: bool = True*)  
This is a decorator that starts an mlflow span for the function it
decorates. If there is an existing trace a span will be appended to it.
If there is no existing trace, a new trace will be created.

It also enables the user to run evaluators when the code is run in
development mode. Evaluators can be run on the span and/or trace
generated for the wrapped function call. The trace evaluator will run if
the parent trace was started and finished by the related decorator call.
The trace will contain all child span information. The span evaluator
will always run. The evaluation results from both evaluators will be
combined and saved to the trace.

This decorator must be used directly on the function to be traced
without any intervening decorators, because it must have access to the
arguments.

@add_tracing(  
name=”assistant_chat_bot”, evaluator=evaluate_helpfulness,

) def ask_chat_bot(user_input: str) -\> dict:

> …

Parameters:  
- **name** – the name of the span to add to existing trace or create if
  no trace exists yet.

- **autolog_frameworks** – an optional list of mlflow supported
  frameworks to autolog

- **evaluator** – an optional function that takes the span created for
  the wrapped function and returns

- **trace** (*decorator. The evaluation results will be saved to the*)

- **trace_evaluator** – an optional function that takes the trace for
  this call stack and returns a dictionary of

- **tracing** (*evaluation results. This evaluator will be triggered if
  the trace was started and finished by the add*)

- **trace**

- **eagerly_evaluate_streamed_results** – optional boolean, defaults to
  true, this determines if all yielded values should be aggregated and
  set as outputs to a single span. This makes evaluation easier, but
  will impact performance if you expect a large number of streamed
  values. If set to false, each yielded value will generate a new span
  on the trace, which can be evaluated post-hoc. Inline evaluators won’t
  be executed. Each span will have a group_id set in their attributes to
  indicate that they are part of the same function call. Each span will
  have an index to indicate what order they arrived in.

Returns:  
A decorator that wraps the function to be traced.

&nbsp;

### domino.aisystems.tracing.init_tracing(*autolog_frameworks: list\[str\] \| None = None*)  
Initialize Mlflow autologging for various frameworks and sets the active
experiment to enable tracing in production. This may be used to
initialize logging and tracing for the AI System in dev and prod modes.

In prod mode, environment variables DOMINO_AI_SYSTEM_IS_PROD,
DOMINO_APP_ID must be set. Call init_tracing before your app starts up
to start logging traces to Domino.

Parameters:  
**autolog_frameworks** – list of frameworks to autolog

&nbsp;

### domino.aisystems.tracing.search_ai_system_traces(*ai_system_id: str*, *ai_system_version: str \| None = None*, *trace_name: str \| None = None*, *start_time: datetime \| None = None*, *end_time: datetime \| None = None*, *page_token: str \| None = None*, *max_results: int \| None = None*) → SearchTracesResponse  
This allows searching for traces that have a certain name and returns a
paginated response of trace summaries that include the spans that were
requested.

Parameters:  
- **ai_system_id** – string, the ID of the AI System to filter by

- **ai_system_version** – string, the version of the AI System to filter
  by, if not provided will search throuh all versions

- **trace_name** – the name of the traces to search for

- **start_time** – python datetime

- **end_time** – python datetime, defaults to now

- **page_token** – page token for pagination. You can use this to
  request the next page of results and may find a page_token in the
  response of the previous search_traces call.

- **max_results** – defaults to 100

Returns:  
a token based pagination response that contains a list of trace summaries  
data: list of TraceSummary page_token: the next page’s token

Return type:  
SearchTracesResponse

&nbsp;

### domino.aisystems.tracing.search_traces(*run_id: str*, *trace_name: str \| None = None*, *start_time: datetime \| None = None*, *end_time: datetime \| None = None*, *page_token: str \| None = None*, *max_results: int \| None = None*) → SearchTracesResponse  
This allows searching for traces that have a certain name and returns a
paginated response of trace summaries that inclued the spans that were
requested.

Parameters:  
- **run_id** – string, the ID of the development mode evaluation run to
  search for traces.

- **trace_name** – the name of the traces to search for

- **start_time** – python datetime

- **end_time** – python datetime, defaults to now

- **page_token** – page token for pagination. You can use this to
  request the next page of results and may find a page_token in the
  response of the previous search_traces call.

- **max_results** – defaults to 100

Returns:  
a token based pagination response that contains a list of trace summaries  
data: list of TraceSummary page_token: the next page’s token

Return type:  
SearchTracesReponse

Modules

|               |     |
|---------------|-----|
| `inittracing` |     |
| `tracing`     |     |


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
[example_airflow_dag.py](https://github.com/dominodatalab/python-domino/blob/Release-1.5.1/examples/example_airflow_dag.py)
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

# Example

    from domino import Domino

    # By and large your commands will run against a single project,
    # so you must specify the full project name
    domino = Domino("chris/canon")

    # List all runs in the project, most-recently queued first
    all_runs = domino.runs_list()['data']

    latest_100_runs = all_runs[0:100]

    print(latest_100_runs)

    # all runs have a commitId (the snapshot of the project when the
    # run starts) and, if the run completed, an "outputCommitId"
    # (the snapshot of the project after the run completed)
    most_recent_run = all_runs[0]

    commitId = most_recent_run['outputCommitId']

    # list all the files in the output commit ID -- only showing the
    # entries under the results directory.  If not provided, will
    # list all files in the project.  Or you can say path=“/“ to
    # list all files
    files = domino.files_list(commitId, path='results/')['data']

    for file in files:
    print file['path'], '->', file['url']

    print(files)

    # Get the content (i.e. blob) for the file you're interested in.
    # blobs_get returns a connection rather than the content, because
    # the content can get quite large and it's up to you how you want
    # to handle it
    print(domino.blobs_get(files[0]['key']).read())

    # Start a run of file main.py using the latest copy of that file
    domino.runs_start(["main.py", "arg1", "arg2"])

    # Start a "direct" command
    domino.runs_start(["echo 'Hello, World!'"], isDirect=True)

    # Start a run of a specific commit
    domino.runs_start(["main.py"], commitId="aabbccddee")

# Manual installation

Because `python-domino` ships with the DSE, normally you do not need to install it.  
This section provides instructions for installing it in another environment or updating it to a newer version.

Starting from version `1.0.6`, `python-domino` is available on PyPI as `dominodatalab`:

    pip install dominodatalab

If you are adding install instructions for `python-domino` to your [Domino Environment](https://support.dominodatalab.com/hc/en-us/articles/115000392643-Compute-Environment-Management) Dockerfile Instructions field, you must add `RUN` to the beginning:

    RUN pip install dominodatalab

To install a specific version of the library from PyPI, such as `1.0.6`:

    pip install dominodatalab==1.0.6

To install a specific version of the library from GitHub, such as
`1.0.6`:

    pip install https://github.com/dominodatalab/python-domino/archive/1.0.6.zip

# License

This library is made available under the Apache 2.0 License. This is an
open-source project of [Domino Data Lab](https://www.dominodatalab.com).
