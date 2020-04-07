from .routes import _Routes
from .helpers import is_version_compatible
from version import PYTHON_DOMINO_VERSION

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

import os
import logging
import requests
import time
import pprint
import re


class Domino:
    def __init__(self, project, api_key=None, host=None):
        self._configure_logging()

        if host is not None:
            host = host
        elif 'DOMINO_API_HOST' in os.environ:
            host = os.environ['DOMINO_API_HOST']
        else:
            raise Exception("Host must be provided, either via the \
                constructor value or through DOMINO_API_HOST environment \
                variable.")

        if api_key is not None:
            self._api_key = api_key
        elif 'DOMINO_USER_API_KEY' in os.environ:
            self._api_key = os.environ['DOMINO_USER_API_KEY']
        else:
            raise Exception("API key must be provided, either via the \
                constructor value or through DOMINO_USER_API_KEY environment \
                variable.")

        owner_username, project_name = project.split("/")
        self._routes = _Routes(host, owner_username, project_name)

        # Get version
        self._version = self.deployment_version().get("version")
        self._logger.info(f"Domino deployment {host} is running version {self._version}")

        # Check version compatibility
        if not is_version_compatible(self._version):
            error_message = f"Domino version: {self._version} is not compatible with " \
                            f"python-domino version: {PYTHON_DOMINO_VERSION}"
            self._logger.error(error_message)
            raise Exception(error_message)

    def _configure_logging(self):
        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)

    def commits_list(self):
        url = self._routes.commits_list()
        return self._get(url)

    def runs_list(self):
        url = self._routes.runs_list()
        return self._get(url)

    def runs_start(self, command, isDirect=False, commitId=None, title=None,
                   tier=None, publishApiEndpoint=None):

        url = self._routes.runs_start()

        request = {
            "command": command,
            "isDirect": isDirect,
            "commitId": commitId,
            "title": title,
            "tier": tier,
            "publishApiEndpoint": publishApiEndpoint
        }

        response = requests.post(url, auth=('', self._api_key), json=request)
        return response.json()

    def runs_start_blocking(self, command, isDirect=False, commitId=None,
                            title=None, tier=None, publishApiEndpoint=None,
                            poll_freq=5, max_poll_time=6000):
        """
        Run a tasks that runs in a blocking loop that periodically checks to
        see if the task is done.  If the task errors an exception is raised.

        parameters
        ----------
        command : list of strings
                  list that containst the name of the file to run in index 0
                  and args in subsequent positions.
                  example:
                  >> domino.runs_start(["main.py", "arg1", "arg2"])

        isDirect : boolean (Optional)
                   Whether or not this command should be passed directly to
                   a shell.

        commitId : string (Optional)
                   The commitId to launch from. If not provided, will launch
                   from latest commit.

        title    : string (Optional)
                   A title for the run

        tier     : string (Optional)
                   The hardware tier to use for the run. Will use project
                   default tier if not provided.

        publishApiEndpoint : boolean (Optional)
                            Whether or not to publish an API endpoint from the
                            resulting output.

        poll_freq : int (Optional)
                    Number of seconds in between polling of the Domino server
                    for status of the task that is running.

        max_poll_time : int (Optional)
                        Maximum number of seconds to wait for a task to
                        complete. If this threshold is exceeded, an exception
                        is raised.
        """
        run_response = self.runs_start(command, isDirect, commitId, title,
                                       tier, publishApiEndpoint)
        run_id = run_response['runId']

        poll_start = time.time()
        while True:
            run_info = self.get_run_info(run_id)
            elapsed_time = time.time() - poll_start

            if elapsed_time >= max_poll_time:
                raise Exception('Run \
                                exceeded maximum time of \
                                {} seconds'.format(max_poll_time))

            if run_info is None:
                raise Exception("Tried to access nonexistent run id {}.".
                                format(run_id))

            output_commit_id = run_info.get('outputCommitId')
            if not output_commit_id:
                time.sleep(poll_freq)
                continue

            # once task has finished running check to see if it was successfull
            else:
                stdout_msg = self.runs_stdout(run_id)

                if run_info['status'] != 'Succeeded':
                    header_msg = ("Remote run {0} \
                                  finished but did not succeed.\n"
                                  .format(run_id))
                    raise Exception(header_msg + stdout_msg)

                logging.info(stdout_msg)
                break

        return run_response

    def run_stop(self, runId, saveChanges=True, commitMessage=None):
        """
        :param runId: string
        :param saveChanges: boolean (Optional) Save or discard run results.
        :param commitMessage: string (Optional)
        """
        url = self._routes.run_stop(runId)
        request = {
            "saveChanges": saveChanges,
            "commitMessage": commitMessage,
            "ignoreRepoState": False
        }
        response = requests.post(url, auth=('', self._api_key), json=request)

        if response.status_code == 400:
            raise Warning("Run ID:" + runId + " not found.")
        else:
            return response

    def runs_status(self, runId):
        url = self._routes.runs_status(runId)
        return self._get(url)

    def get_run_info(self, run_id):
        for run_info in self.runs_list()['data']:
            if run_info['id'] == run_id:
                return run_info

    def runs_stdout(self, runId):
        """
        Get std out emitted by a particular run.

        parameters
        ----------
        runId : string
                the id associated with the run.
        """
        url = self._routes.runs_stdout(runId)
        # pprint.pformat outputs a string that is ready to be printed
        return pprint.pformat(self._get(url)['stdout'])

    def files_list(self, commitId, path='/'):
        url = self._routes.files_list(commitId, path)
        return self._get(url)

    def files_upload(self, path, file):
        url = self._routes.files_upload(path)
        return self._put_file(url, file)

    def blobs_get(self, key):
        self._validate_blob_key(key)
        url = self._routes.blobs_get(key)
        return self._open_url(url)

    def fork_project(self, target_name):
        url = self._routes.fork_project()
        request = {"overrideProjectName": target_name}
        response = requests.post(url, auth=('', self._api_key), data=request)
        return response.status_code

    def endpoint_state(self):
        url = self._routes.endpoint_state()
        return self._get(url)

    def endpoint_unpublish(self):
        url = self._routes.endpoint()
        response = requests.delete(url, auth=('', self._api_key))
        return response

    def endpoint_publish(self, file, function, commitId):
        url = self._routes.endpoint_publish()

        request = {
            "commitId": commitId,
            "bindingDefinition": {
                "file": file,
                "function": function
            }
        }

        response = requests.post(url, auth=('', self._api_key), json=request)
        return response

    def deployment_version(self):
        url = self._routes.deployment_version()
        return self._get(url)

    def project_create(self, owner_username, project_name):
        self.requires_at_least("1.53.0.0")
        url = self._routes.project_create()
        request = {
            'owner': owner_username,
            'name': project_name
        }
        response = requests.post(url, auth=('', self._api_key), data=request,
                                 allow_redirects=False)
        disposition = parse_play_flash_cookie(response)
        if disposition.get("error"):
            raise Exception(disposition.get("message"))
        else:
            return disposition

    def collaborators_get(self):
        self.requires_at_least("1.53.0.0")
        url = self._routes.collaborators_get()
        return self._get(url)

    def collaborators_add(self, usernameOrEmail, message=""):
        self.requires_at_least("1.53.0.0")
        url = self._routes.collaborators_add()
        request = {
            'collaboratorUsernameOrEmail': usernameOrEmail,
            'welcomeMessage': message
        }
        response = requests.post(url, auth=('', self._api_key), data=request,
                                 allow_redirects=False)
        disposition = parse_play_flash_cookie(response)
        if disposition.get("error"):
            raise Exception(disposition.get("message"))
        else:
            return disposition

    # App functions
    def app_publish(self, unpublishRunningApps=True, hardwareTierId=None):
        if unpublishRunningApps is True:
            self.app_unpublish()
        app_id = self._app_id
        url = self._routes.app_publish(app_id)
        request = {
            "hardwareTierId": hardwareTierId
        }
        response = requests.post(url, auth=('', self._api_key), json=request)
        return response

    def app_unpublish(self):
        app_id = self._app_id
        url = self._routes.app_unpublish(app_id)
        response = requests.post(url, auth=('', self._api_key))
        return response

    # Environment functions
    def environments_list(self):
        self.requires_at_least("2.5.0")
        url = self._routes.environments_list()
        return self._get(url)

    # Model Manager functions
    def models_list(self):
        self.requires_at_least("2.5.0")
        url = self._routes.models_list()
        return self._get(url)

    def model_publish(self, file, function, environment_id, name,
                      description, files_to_exclude=[]):
        self.requires_at_least("2.5.0")

        url = self._routes.model_publish()

        request = {
            "name": name,
            "description": description,
            "projectId": self._project_id,
            "file": file,
            "function": function,
            "excludeFiles": files_to_exclude,
            "environmentId": environment_id
        }

        response = requests.post(url, auth=('', self._api_key), json=request)
        return response.json()

    def model_versions_get(self, model_id):
        self.requires_at_least("2.5.0")
        url = self._routes.model_versions_get(model_id)
        return self._get(url)

    def model_version_publish(self, model_id, file, function, environment_id,
                              name, description, files_to_exclude=[]):
        self.requires_at_least("2.5.0")

        url = self._routes.model_version_publish(model_id)

        request = {
            "name": name,
            "description": description,
            "projectId": self._project_id,
            "file": file,
            "function": function,
            "excludeFiles": files_to_exclude,
            "environmentId": environment_id
        }

        response = requests.post(url, auth=('', self._api_key), json=request)
        return response.json()

    # Helper methods
    def _get(self, url):
        return requests.get(url, auth=('', self._api_key)).json()

    def _put_file(self, url, file):
        return requests.put(url, data=file, auth=('', self._api_key))

    def _open_url(self, url):
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self._routes.host, '', self._api_key)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        return opener.open(url)

    def _validate_blob_key(self, key):
        regex = re.compile("^\\w{40,40}$")
        if not regex.match(key):
            raise Exception(("Blob key should be 40 alphanumeric charachters. "
                             "Perhaps you passed a file path on accident? "
                             "If you have a file path and want to get the "
                             "file, use files_list to get the blob key."))

    def requires_at_least(self, at_least_version):
        if at_least_version > self._version:
            raise Exception("You need at least version {} but your deployment \
                            seems to be running {}".format(
                            at_least_version, self._version))

    # Workaround to get project ID which is needed for some model functions
    @property
    def _project_id(self):
        url = self._routes.find_project_by_owner_name_and_project_name_url()
        key = "id"
        response = self._get(url)
        if key in response.keys():
            return response[key]

    @property
    def _app_id(self):
        url = self._routes.app_list(self._project_id)
        response = self._get(url)
        if len(response) != 0:
            app = response[0]
        else:
            raise Exception(f"No App found in project")
        key = "id"
        if key in app.keys():
            app_id = app[key]
        else:
            app_id = None
        return app_id


def parse_play_flash_cookie(response):
    flash_cookie = response.cookies['PLAY_FLASH']
    messageType, message = flash_cookie.split("=")
    # Format message into user friendly string
    message = urllib2.unquote(message).replace("+", " ")
    # Discern error disposition
    if(messageType == "dominoFlashError"):
        error = True
    else:
        error = False
    return dict(messageType=messageType, message=message, error=error)
