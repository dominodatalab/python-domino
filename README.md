# python-domino

Python bindings for the Domino API.

Permits interaction with a Domino deployment from Python using the [Domino API](https://dominodatalab.github.io/api-docs/).

## Version Compatibility Matrix

`python-domino` library is compatible with different versions of the `Domino`:

| Domino Versions | Python-Domino |
| --------------- |:-------------:|
| 3.6.x or Lower  | [0.3.5](http://github.com/dominodatalab/python-domino/archive/0.3.5.zip)         |
| 4.1.0 or Higher | [1.0.0](https://github.com/dominodatalab/python-domino/archive/master.zip)         |

## Installation 

At this time, these Domino Python bindings are not in PyPi. You can install the latest version of this package from our Github `master` branch with the following:

    pip install https://github.com/dominodatalab/python-domino/archive/master.zip

If you are adding install instructions for `python-domino` to your [Domino Environment](https://support.dominodatalab.com/hc/en-us/articles/115000392643-Compute-Environment-Management) `Dockerfile Instructions` field, you must add `RUN` to the beginning:

    RUN pip install https://github.com/dominodatalab/python-domino/archive/master.zip

You can also add `python-domino` to your `requirements.txt` file with the following syntax:

    -f git+git://github.com/dominodatalab/python-domino.git

Note: To install lower version of library, for example `0.3.5` use the following command:
    
    pip install https://github.com/dominodatalab/python-domino/archive/0.3.5.zip

## Overview

### Setting up the connection

You can set up the connection by creating new instance of `Domino`.

<hr>

### *class* Domino(project, api_key=None, host=None, domino_token_file=None)

The parameters are:

* *project:* A project identifier (in the form of ownerusername/projectname)
* *api_key:* (Optional) An API key to authenticate with. If not provided the library will expect to find one
  in the DOMINO_USER_API_KEY environment variable.
* *host:* (Optional) A host URL. If not provided the library will expect to find one in the DOMINO_API_HOST
  environment variable.
* *domino_token_file:* (Optional) Path to domino token file containing auth token. If not provided the library will expect to find one
in the DOMINO_TOKEN_FILE environment variable.

Note: In case both api_key and domino_token_file are available, then preference will be given to domino_token_file.
  
<hr>

## Methods


<hr>

### runs_list()

List the runs on the selected project.

<hr>

### runs_start(*command, isDirect, commitId, title, tier, publishApiEndpoint*)

Start a new run on the selected project. The parameters are:

* *command:* The command to run as an array of strings where members of the array represent arguments
  of the command. E.g. `["main.py", "hi mom"]`
* *isDirect:* (Optional) Whether or not this command should be passed directly to a shell.
* *commitId:* (Optional) The commitId to launch from. If not provided, will launch from latest commit.
* *title:* (Optional) A title for the run.
* *tier:* (Optional) The hardware tier to use for the run. This is the human-readable name of the hardware tier, such as "Free", "Small", or "Medium".  Will use project default tier if not provided. 
* *publishApiEndpoint:* (Optional) Whether or not to publish an API endpoint from the resulting output.

<hr>

### runs_start_blocking(*command, isDirect, commitId, title, tier, publishApiEndpoint, poll_freq=5, max_poll_time=6000*)

Same as method `run_start` except make a blocking request that waits until job is finished.

* *command:* The command to run as an array of strings where members of the array represent arguments
  of the command. E.g. `["main.py", "hi mom"]`
* *isDirect:* (Optional) Whether or not this command should be passed directly to a shell.
* *commitId:* (Optional) The commitId to launch from. If not provided, will launch from latest commit.
* *title:* (Optional) A title for the run.
* *tier:* (Optional) The hardware tier to use for the run. Will use project default tier if not provided.
* *publishApiEndpoint:* (Optional) Whether or not to publish an API endpoint from the resulting output.
* *poll_freq:* (Optional) Number of seconds in between polling of the Domino server for status of the task that is running.
* *max_poll_time:* (Optional) Maximum number of seconds to wait for a task to complete.  If this threshold is exceeded, an exception is raised.
* *retry_count:* (Optional) Maximum number of retry to do while polling (in-case of transient http errors). If this threshold is exceeded, an exception is raised.

<hr>

### run_stop(*runId, saveChanges=True, commitMessage=None*):

Stop an existing run in the selected project. The parameters are:

* *runId:* string that identifies the run
* *saveChanges:* (Defaults to True) If false, run results will be discarded.
* *commitMessage:* (Optional) Adds a Domino commit message to the run commit. 

<hr>

### runs_stdout(*runId*)

Get stdout emitted by a particular run.  The parameters are:

* *runId:* string that identifies the run

<hr>

### files_list(*commitId, path*)

List the files in a folder in the Domino project. The parameters are:

* *commitId:* The commitId to list files from.
* *path:* (Defaults to "/") The path to list from.

<hr>

### files_upload(*path, file*)

Upload a Python file object into the specified path inside the project. See `examples/upload_file.py` for an example. The parameters, both of which are required, are:

* *path:* The path to save the file to. For example, `/README.md` will write to the root directory of the project while `/data/numbers.csv` will save the file to a subfolder named `data` (if the `data` folder does not yet exist, it will be created)
* *file:* A Python file object. For example, `f = open("authors.txt","rb")`

<hr>

### blobs_get(*key*)

Retrieve a file from the Domino server by blob key. The parameters are:

* **key:** The key of the file to fetch from the blob server.

<hr>

### app_publish(*unpublishRunningApps=True*, *hardwareTierId=None*)

Publishes an app in the Domino project, or republish an existing app. The parameters are:

* *unpublishRunningApps:* (Defaults to True) Will check for any active app instances in the current project and unpublish them before publishing.
* *hardwareTierId:* (Optional) Will launch the app on the specified hardware tier. Only applies for Domino 3.4+.

<hr>

### app_unpublish()

Stops all running apps in the Domino project.  

<hr>

## License

This library is made available under the Apache 2.0 License.
This is an open-source project of [Domino Data Lab](https://www.dominodatalab.com).
