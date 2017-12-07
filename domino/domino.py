from .routes import _Routes

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

import os
import logging
import requests
import time
import pprint


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

        self._logger.info('Initializing Domino API with host ' + host)

        owner_username = project.split("/")[0]
        project_name = project.split("/")[1]
        self._routes = _Routes(host, owner_username, project_name)

        if api_key is not None:
            self._api_key = api_key
        elif 'DOMINO_USER_API_KEY' in os.environ:
            self._api_key = os.environ['DOMINO_USER_API_KEY']
        else:
            raise Exception("API key must be provided, either via the \
                constructor value or through DOMINO_USER_API_KEY environment \
                variable.")

        # Get version
        self._version = self.deployment_version().get("version")
        print("Your Domino deployment is running version {}".format(self._version))

    def _configure_logging(self):
        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)

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
                  list that containst the name of the file to run in index 0 and
                  args in subsequent positions.
                  example:
                  >> domino.runs_start(["main.py", "arg1", "arg2"])

        isDirect : boolean (Optional)
                   Whether or not this command should be passed directly to a shell.

        commitId : string (Optional)
                   The commitId to launch from. If not provided, will launch from latest commit.

        title    : string (Optional)
                   A title for the run

        tier     : string (Optional)
                   The hardware tier to use for the run. Will use project default
                   tier if not provided.

        publishApiEndpoint : boolean (Optional)
                            Whether or not to publish an API endpoint from the resulting output.

        poll_freq : int (Optional)
                    Number of seconds in between polling of the Domino server for
                    status of the task that is running.

        max_poll_time : int (Optional)
                        Maximum number of seconds to wait for a task to complete.
                        If this threshold is exceeded, an exception is raised.
        """
        run_response = self.runs_start(command, isDirect, commitId, title,
                                       tier, publishApiEndpoint)
        run_id = run_response['runId']

        poll_start = time.time()
        while True:
            run_info = self.get_run_info(run_id)
            elapsed_time = time.time() - poll_start

            if elapsed_time >= max_poll_time:
                raise Exception('Run exceeded maximum time of {} seconds'.format(max_poll_time))

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
                    header_msg = ("Remote run {0} finished but did not succeed.\n"
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
        url = self._routes.blobs_get(key)
        return self._open_url(url)

    def fork_project(self, target_name):
        url = self._routes.fork_project()
        request = { "overrideProjectName" : target_name}
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
    def app_publish(self, unpublishRunningApps=True):
        if unpublishRunningApps == True:
            self.app_unpublish()
        url = self._routes.app_publish()
        request = {"language": "App"}
        response = requests.post(url, auth=('', self._api_key), json=request)
        return response
    
    def app_unpublish(self):
        apps = [r for r in self.runs_list()['data'] if r['notebookName'] == 'App' and r['isCompleted'] == False]
        for app in apps:
            self.run_stop(app['id'])
    

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

    def requires_at_least(self, at_least_version):
        if at_least_version > self._version:
            raise Exception("You need at least version {} but your deployment \
                            seems to be running {}".format(
                            at_least_version, self._version))


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
