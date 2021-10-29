from typing import Optional, Tuple, List

from .routes import _Routes
from .helpers import *
from .http_request_manager import _HttpRequestManager
from .authentication import get_auth_by_type
from .exceptions import *

from domino._version import __version__

import os
import logging
import requests
import functools
import time
import pprint
import re
import polling2
from bs4 import BeautifulSoup


class Domino:
    def __init__(self, project, api_key=None, host=None, domino_token_file=None, auth_token=None):

        self._configure_logging()

        _host = host or os.getenv(DOMINO_HOST_KEY_NAME)
        assert _host, ("Host must be supplied as a parameter or through the "
                       f"{DOMINO_HOST_KEY_NAME} environment variable.")
        host = clean_host_url(_host)

        try:
            owner_username, project_name = project.split("/")
            self._routes = _Routes(host, owner_username, project_name)
        except ValueError as e:
            self._logger.error(f"Project {project} must be given in the form username/projectname")
            raise

        domino_token_file = domino_token_file or os.getenv(DOMINO_TOKEN_FILE_KEY_NAME)
        api_key = api_key or os.getenv(DOMINO_USER_API_KEY_KEY_NAME)

        # This call sets self.request_manager
        self.authenticate(api_key, auth_token, domino_token_file)

        # Get version
        self._version = self.deployment_version().get("version")
        self._logger.info(f"Domino deployment {host} is running version {self._version}")

        # Check version compatibility
        if not is_version_compatible(self._version):
            error_message = (f"Domino version: {self._version} is not compatible with "
                             f"python-domino version: {__version__}")
            self._logger.error(error_message)
            raise Exception(error_message)

    @property
    def log(self):
        try:
            return self._logger
        except AttributeError:
            self._configure_logging()
            return self._logger

    def _configure_logging(self):
        logging_level = logging.getLevelName(os.getenv(DOMINO_LOG_LEVEL_KEY_NAME, "INFO").upper())
        logging.basicConfig(level=logging_level)
        self._logger = logging.getLogger(__name__)

    def authenticate(self, api_key=None, auth_token=None, domino_token_file=None):
        """
        Method to authenticate the request manager. An existing domino client object can
        use this with a new token if the existing credentials expire.
        """
        self.request_manager = _HttpRequestManager(get_auth_by_type(api_key=api_key,
                                                                    auth_token=auth_token,
                                                                    domino_token_file=domino_token_file))

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
        try:
            response = self.request_manager.post(url, json=request)
            return response.json()
        except ReloginRequiredException:
            self._logger.info(f" You need to log in to the Domino UI to start the run. Please do it at {self._routes.host}/relogin?redirectPath=/")

    def runs_start_blocking(self, command, isDirect=False, commitId=None,
                            title=None, tier=None, publishApiEndpoint=None,
                            poll_freq=5, max_poll_time=6000, retry_count=5):
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

        retry_count : int (Optional)
                        Maximum number of retry to do while polling
                        (in-case of transient http errors). If this
                        threshold exceeds, an exception is raised.
        """
        run_response = self.runs_start(command, isDirect, commitId, title,
                                       tier, publishApiEndpoint)
        run_id = run_response['runId']

        poll_start = time.time()
        current_retry_count = 0
        while True:
            try:
                run_info = self.get_run_info(run_id)
                if run_info is None:
                    raise RunNotFoundException(f"Tried to access nonexistent run id {run_id}")
                current_retry_count = 0
            except (requests.exceptions.RequestException, RunNotFoundException) as e:
                current_retry_count += 1
                self.log.warning(f'Failed to get run info for runId: {run_id} : {e}')
                if current_retry_count > retry_count:
                    raise Exception(f'Cannot get run info, max retry {retry_count} exceeded') from None
                else:
                    self.log.info(f'Retrying ({current_retry_count}/{retry_count}) getting run info ...')
                    time.sleep(poll_freq)
                    continue

            elapsed_time = time.time() - poll_start

            if elapsed_time >= max_poll_time:
                raise Exception('Run \
                                exceeded maximum time of \
                                {} seconds'.format(max_poll_time))

            output_commit_id = run_info.get('outputCommitId')
            if not output_commit_id:
                time.sleep(poll_freq)
                continue

            # once task has finished running check to see if it was successfull
            else:
                stdout_msg = self.get_run_log(runId=run_id, includeSetupLog=False)

                if run_info['status'] != 'Succeeded':
                    self.process_log(stdout_msg)
                    raise RunFailedException(f"Remote run {run_id} finished but did not succeed.")

                break

        return run_response

    def run_stop(self, runId, saveChanges=True):
        self.log.warning("Use job_stop method instead")
        return self.job_stop(job_id=runId, commit_results=saveChanges)

    def runs_status(self, runId):
        url = self._routes.runs_status(runId)
        return self._get(url)

    def get_run_log(self, runId, includeSetupLog=True):
        """
        Get the unified log for a run (setup + stdout).

        parameters
        ----------
        runId : string
                the id associated with the run.
        includeSetupLog : bool
                whether or not to include the setup log in the output.
        """

        url = self._routes.runs_stdout(runId)

        logs = list()

        if includeSetupLog:
            logs.append(self._get(url)["setup"])

        logs.append(self._get(url)["stdout"])

        return "\n".join(logs)

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

    def job_start(
            self,
            command: str,
            commit_id: Optional[str] = None,
            hardware_tier_name: Optional[str] = None,
            environment_id: Optional[str] = None,
            on_demand_spark_cluster_properties: Optional[dict] = None,
            compute_cluster_properties: Optional[dict] = None,
            external_volume_mounts: Optional[List[str]] = None,
    ) -> dict:
        """
        Starts a Domino Job via V4 API
        :param command:                             string
                                                    Command to execute in Job
                                                    >> domino.job_start(command="main.py arg1 arg2")
        :param commit_id:                           string (Optional)
                                                    The commitId to launch from. If not provided, will launch
                                                    from latest commit.
        :param hardware_tier_name:                  string (Optional)
                                                    The hardware tier NAME to launch job in. If not provided
                                                    it will use the default hardware tier for the project
        :param environment_id:                      string (Optional)
                                                    The environment id to launch job with. If not provided
                                                    it will use the default environment for the project
        :param on_demand_spark_cluster_properties:  dict (Optional)
                                                    This field is deprecated. Please use compute_cluster_properties.
                                                    The following properties can be provided in spark cluster
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
        :param compute_cluster_properties:          dict (Optional)
                                                    The compute cluster properties definition contains parameters for
                                                    launching any Domino supported compute cluster for a job. Use this
                                                    to launch a job that uses a compute cluster instead of
                                                    the deprecated on_demand_spark_cluster_properties field. If
                                                    on_demand_spark_cluster_properties and compute_cluster_properties
                                                    are both present, on_demand_spark_cluster_properties will be ignored.

                                                    compute_cluster_properties contains the following fields:
                                                    {
                                                        "clusterType": <string, one of "Ray", "Spark">,
                                                        "computeEnvironmentId": <string, The environment ID for the cluster's nodes>,
                                                        "computeEnvironmentRevisionSpec": <one of "ActiveRevision", "LatestRevision",
                                                        {"revisionId":"<environment_revision_id>"} (optional)>,
                                                        "masterHardwareTierId": <string, the Hardware tier ID for the cluster's master node>,
                                                        "workerCount": <number, the total workers to spawn for the cluster>,
                                                        "workerHardwareTierId": <string, The Hardware tier ID for the cluster workers>,
                                                        "workerStorage": <{ "value": <number>, "unit": <one of "GiB", "MB"> },
                                                        The disk storage size for the cluster's worker nodes (optional)>
                                                        "maxWorkerCount": <number, The max number of workers allowed. When
                                                        this configuration exists, autoscaling is enabled for the cluster and
                                                        'workerCount' is interpreted as the min number of workers allowed in the cluster
                                                        (optional)>
                                                    }
        :param external_volume_mounts:              list of string (Optional)
                                                    External volume mount ids to mount to run. If not provided will launch with
                                                    no external volume mounts mounted.
        :return: Returns created Job details (number, id etc)
        """
        def validate_on_demand_spark_cluster_properties(max_execution_slot_per_user):
            self.log.debug(f"Validating spark cluster properties: {on_demand_spark_cluster_properties}")
            validations = {
                'executorCount': lambda ec: validate_spark_executor_count(int(ec), max_execution_slot_per_user),
                'computeEnvironmentId': lambda com_env_id: self._validate_environment_id(com_env_id),
                'executorHardwareTierId': lambda exec_hwd_tier_id: self._validate_hardware_tier_id(exec_hwd_tier_id),
                'masterHardwareTierId': lambda master_hwd_tier_id: self._validate_hardware_tier_id(master_hwd_tier_id),
                'executorStorageMB': lambda exec_storage_mb: True
            }
            if 'computeEnvironmentId' not in on_demand_spark_cluster_properties:
                raise MissingRequiredFieldException(f"Mandatory field computeEnvironmentId not passed in spark properties")
            for k, v in on_demand_spark_cluster_properties.items():
                if not validations.get(k, lambda x: False)(v):
                    raise MalformedInputException(f"Invalid spark property {k}:{v} found")

        def validate_spark_executor_count(executor_count, max_executor_count):
            if executor_count <= max_executor_count:
                return True
            else:
                raise MalformedInputException(f"executor count: {executor_count} exceeding max executor count: {max_executor_count}")

        def get_default_spark_settings():
            self.log.debug(f"Getting default spark settings")
            default_spark_setting_url = self._routes.default_spark_setting(self._project_id)
            return self.request_manager.get(default_spark_setting_url).json()

        def validate_is_on_demand_spark_supported():
            if not is_on_demand_spark_cluster_supported(self._version):
                raise OnDemandSparkClusterNotSupportedException(
                    f"Your domino deployment version {self._version} does not support on demand spark cluster. "
                    f"Minimum support version {MINIMUM_ON_DEMAND_SPARK_CLUSTER_SUPPORT_DOMINO_VERSION}")

        def validate_distributed_compute_cluster_properties():
            if not is_compute_cluster_properties_supported(self._version):
                raise UnsupportedFieldException(f"'compute_cluster_properties' is not supported in Domino {self._version}.")

            required_keys = ["clusterType", "computeEnvironmentId", "masterHardwareTierId", "workerHardwareTierId", "workerCount"]
            for key in required_keys:
                try:
                    compute_cluster_properties[key]
                except KeyError:
                    raise MissingRequiredFieldException(f"{key} is required in compute_cluster_properties")

            if not is_cluster_type_supported(self._version, compute_cluster_properties["clusterType"]):
                supported_types = [ct for ct,min_version in CLUSTER_TYPE_MIN_SUPPORT if is_cluster_type_supported(self._version, ct)]
                supported_types_str = ", ".join(supported_types)
                raise MalformedInputException(
                    f"Domino {self._version} does not support cluster type {compute_cluster_properties['clusterType']}." +
                    f" This version of Domino supports the following cluster types: {supported_types_str}"
                )


            def throw_if_information_invalid(key: str, info: dict) -> bool:
                try:
                    self._validate_information_data_type(info)
                except Exception as e:
                    raise MalformedInputException(f"{key} in compute_cluster_properties failed validation: {e}")

            if "workerStorage" in compute_cluster_properties:
                throw_if_information_invalid("workerStorage", compute_cluster_properties["workerStorage"])

            if compute_cluster_properties["workerCount"] < 1:
                raise MalformedInputException("compute_cluster_properties.workerCount must be greater than 0")

            if "maxWorkerCount" in compute_cluster_properties and not is_comute_cluster_autoscaling_supported(self._version):
                raise UnsupportedFieldException(f"'maxWorkerCount' is not supported in Domino {self._version}.")

        def validate_is_external_volume_mounts_supported():
            if not is_external_volume_mounts_supported(self._version):
                raise ExternalVolumeMountsNotSupportedException(
                    f"Your domino deployment version {self._version} does not support external volume mounts. "
                    f"Minimum support version {MINIMUM_EXTERNAL_VOLUME_MOUNTS_SUPPORT_DOMINO_VERSION}")

        spark_cluster_properties = None
        validated_compute_cluster_properties = None

        if commit_id is not None:
            self._validate_commit_id(commit_id)
        if hardware_tier_name is not None:
            self._validate_hardware_tier_name(hardware_tier_name)
        if environment_id is not None:
            self._validate_environment_id(environment_id)
        if external_volume_mounts is not None:
            validate_is_external_volume_mounts_supported()
        if compute_cluster_properties is not None:
            validate_distributed_compute_cluster_properties()

            validated_compute_cluster_properties = compute_cluster_properties.copy()
            validated_compute_cluster_properties["masterHardwareTierId"] = { "value": compute_cluster_properties["masterHardwareTierId"] }
            validated_compute_cluster_properties["workerHardwareTierId"] = { "value": compute_cluster_properties["workerHardwareTierId"] }

        elif on_demand_spark_cluster_properties is not None:
            validate_is_on_demand_spark_supported()
            default_spark_setting = get_default_spark_settings()
            max_execution_slot = default_spark_setting['maximumExecutionSlotsPerUser']
            default_executor_hardware_tier = default_spark_setting['executorHardwareTierId']
            default_master_hardware_tier = default_spark_setting['masterHardwareTierId']
            validate_on_demand_spark_cluster_properties(max_execution_slot)
            executor_hardware_tier_id = on_demand_spark_cluster_properties.get('executorHardwareTierId',
                                                                               default_executor_hardware_tier)
            master_hardware_tier_id = on_demand_spark_cluster_properties.get('masterHardwareTierId',
                                                                             default_master_hardware_tier)
            executor_count = int(on_demand_spark_cluster_properties.get('executorCount', 1))
            compute_environment_id = on_demand_spark_cluster_properties.get('computeEnvironmentId')
            executor_storage = int(on_demand_spark_cluster_properties.get('executorStorageMB', 0))
            spark_cluster_properties = {
                "computeEnvironmentId": compute_environment_id,
                "executorCount": executor_count,
                "executorHardwareTierId": executor_hardware_tier_id,
                "executorStorageMB": executor_storage,
                "masterHardwareTierId": master_hardware_tier_id
            }

        url = self._routes.job_start()
        payload = {
          "projectId": self._project_id,
          "commandToRun": command,
          "commitId": commit_id,
          "overrideHardwareTierName": hardware_tier_name,
          "onDemandSparkClusterProperties": spark_cluster_properties,
          "computeClusterProperties": validated_compute_cluster_properties,
          "environmentId": environment_id,
          "externalVolumeMounts": external_volume_mounts
        }
        try:
            response = self.request_manager.post(url, json=payload)
            return response.json()
        except ReloginRequiredException:
            self._logger.info(f" You need to log in to the Domino UI to start the job. Please do it at {self._routes.host}/relogin?redirectPath=/")

    def job_stop(self, job_id: str, commit_results: bool = True):
        """
        Stops the Job with given job_id
        :param job_id: The job identifier
        :param commit_results: Boolean representing to commit results to file
        """
        url = self._routes.job_stop()
        request = {
            "projectId": self._project_id,
            "jobId": job_id,
            "commitResults": commit_results
        }
        response = self.request_manager.post(url, json=request)
        return response

    def job_status(self, job_id: str) -> dict:
        """
        Gets the status of job with given job_id
        :param job_id: The job identifier
        :return: The details
        """
        return self.request_manager.get(
            self._routes.job_status(job_id)
        ).json()

    def job_start_blocking(self, poll_freq: int = 5, max_poll_time: int = 6000,
                           ignore_exceptions: Tuple = (requests.exceptions.RequestException,),
                           **kwargs) -> dict:
        """
        Starts a job in a blocking loop, periodically polling for status of job
        is complete. Will ignore intermediate request exception.
        :param poll_freq: int (Optional) polling frequency interval in seconds
        :param max_poll_time: int (Optional) max poll time in seconds
        :param ignore_exceptions: tuple (Optional) a tuple of exceptions that can be ignored
        :param kwargs: Additional arguments to be passed to job_start
        :return:
        """
        def get_job_status(job_identifier):
            status = self.job_status(job_identifier)
            self.log.info(f"Polling Job: {job_identifier} status is completed: {status['statuses']['isCompleted']}")
            if status['statuses']['executionStatus'] == "Failed":
                raise RunFailedException(f"Run Status Failed for run: {job_identifier}")
            return status
        job = self.job_start(**kwargs)
        job_id = job['id']
        job_status = polling2.poll(
            target=lambda: get_job_status(job_id),
            check_success=lambda status: status['statuses']['isCompleted'],
            ignore_exceptions=ignore_exceptions,
            timeout=max_poll_time,
            step=poll_freq,
            log_error=self.log.level
        )
        stdout_msg = self.get_run_log(runId=job_id, includeSetupLog=False)
        self.process_log(stdout_msg)
        return job_status

    def files_list(self, commitId, path='/'):
        url = self._routes.files_list(commitId, path)
        return self._get(url)

    def files_upload(self, path, file):
        url = self._routes.files_upload(path)
        return self._put_file(url, file)

    def blobs_get(self, key):
        self._validate_blob_key(key)
        url = self._routes.blobs_get(key)
        return self.request_manager.get_raw(url)

    def fork_project(self, target_name):
        url = self._routes.fork_project(self._project_id)
        request = {"name": target_name}
        response = self.request_manager.post(url, json=request)
        return response

    def endpoint_state(self):
        url = self._routes.endpoint_state()
        return self._get(url)

    def endpoint_unpublish(self):
        url = self._routes.endpoint()
        response = self.request_manager.delete(url)
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

        response = self.request_manager.post(url, json=request)
        return response

    def deployment_version(self):
        url = self._routes.deployment_version()
        return self._get(url)

    def project_create(self, project_name, owner_username=None):
        url = self._routes.project_create()
        data = {
            'projectName': project_name,
            'ownerOverrideUsername': owner_username
        }
        response = self.request_manager.post(url, data=data, headers=self._csrf_no_check_header)
        return response

    def project_archive(self, project_name):
        """Delete the project with the given name"""
        all_owned_projects = self.projects_list(show_completed=True)
        for p in all_owned_projects:
            if p['name'] == project_name:
                url = self._routes.project_archive(project_id=p['id'])
                self.request_manager.delete(url)
                break
        else:
            raise ProjectNotFoundException(project_name)

    def projects_list(self, relationship="Owned", show_completed=False):
        url = self._routes.projects_list()

        valid_relationships = ["Owned", "Collaborating", "Suggesting", "Popular"]
        if relationship not in valid_relationships:
            raise ValueError(f"relationship must be one of {valid_relationships}: {relationship}")

        query = {"relationship": relationship, "showCompleted": str(show_completed).lower()}
        response = self.request_manager.get(url, params=query)
        return response.json()

    def collaborators_get(self):
        self.requires_at_least("1.53.0.0")
        url = self._routes.collaborators_get()
        return self._get(url)

    def get_user_id(self, username_or_email):
        """
        Return the user ID of the the user account matching the given search criteria.

        Args:
            username_or_email (str): the username or email account of a user

        Return:
           user_id (str): the matching user ID, or None if not found
        """
        url = self._routes.users_get()
        response = self.request_manager.get(url)
        users = response.json()

        user_id = None
        for user in users:
            if username_or_email in (user.get('userName'), user.get('email')):
                user_id = user['id']
                break
        return user_id

    def collaborators_add(self, username_or_email, message=""):
        self.requires_at_least("1.53.0.0")

        user_id = self.get_user_id(username_or_email)

        if user_id is None:
            raise UserNotFoundException(f"Could not add collaborator matching {username_or_email}")

        url = self._routes.collaborators_add(self._project_id)
        request = {
            "collaboratorId": user_id,
            "projectRole": "Contributor"
        }

        response = self.request_manager.post(url, json=request)
        return response

    def collaborators_remove(self, username_or_email):
        self.requires_at_least("1.53.0.0")

        user_id = self.get_user_id(username_or_email)

        if user_id is None:
            raise UserNotFoundException(f"Could not remove collaborator matching {username_or_email}")

        url = self._routes.collaborators_remove(self._project_id, user_id)

        response = self.request_manager.delete(url)
        return response

    # App functions
    def app_publish(self, unpublishRunningApps=True, hardwareTierId=None):
        if unpublishRunningApps:
            self.app_unpublish()
        app_id = self._app_id
        if app_id is None:
            # No App Exists creating one
            app_id = self.__app_create(hardware_tier_id=hardwareTierId)
        url = self._routes.app_start(app_id)
        request = {
            'hardwareTierId': hardwareTierId
        }
        response = self.request_manager.post(url, json=request)
        return response

    def app_unpublish(self):
        app_id = self._app_id
        if app_id is None:
            return
        status = self.__app_get_status(app_id)
        self.log.debug(f"App {app_id} status={status}")
        if status and status != 'Stopped' and status != 'Failed':
            url = self._routes.app_stop(app_id)
            response = self.request_manager.post(url)
            return response

    def __app_get_status(self, id) -> Optional[str]:
        app_id = self._app_id
        if app_id is None:
            return None
        url = self._routes.app_get(app_id)
        response = self.request_manager.get(url).json()
        return response.get('status', None)

    def __app_create(self, name: str = "", hardware_tier_id: str = None) -> str:
        """
        Private method to create app

        :param name: Optional field to set title of app
        :param hardware_tier_id: Optional field to override hardware tier
        :return: Id of newly created App (Un-Published)
        """
        url = self._routes.app_create()
        request_payload = {
            'modelProductType': 'APP',
            'projectId': self._project_id,
            'name': name,
            'owner': '',
            'created': time.time_ns(),
            'lastUpdated': time.time_ns(),
            'status': '',
            'media': [],
            'openUrl': '',
            'tags': [],
            'stats': {
                'usageCount': 0
            },
            'appExtension': {
                'appType': ''
            },
            'id': '000000000000000000000000',
            'permissionsData': {
                'visibility': 'GRANT_BASED',
                'accessRequestStatuses': {},
                'pendingInvitations': [],
                'discoverable': True,
                'appAccessStatus': 'ALLOWED'
            }
        }
        r = self.request_manager.post(url, json=request_payload)
        response = r.json()
        key = "id"
        if key in response.keys():
            app_id = response[key]
        else:
            raise Exception("Cannot create app")
        return app_id

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

        response = self.request_manager.post(url, json=request)
        return response.json()

    def model_versions_get(self, model_id):
        self.requires_at_least("2.5.0")
        url = self._routes.model_versions_get(model_id)
        return self._get(url)

    def model_version_publish(self, model_id, file, function, environment_id,
                              description, files_to_exclude=[]):
        self.requires_at_least("2.5.0")

        url = self._routes.model_version_publish(model_id)

        request = {
            "description": description,
            "projectId": self._project_id,
            "file": file,
            "function": function,
            "excludeFiles": files_to_exclude,
            "environmentId": environment_id
        }

        response = self.request_manager.post(url, json=request)
        return response.json()

    def model_version_export(self, model_id, model_version_id, registry_host,
                             registry_username, registry_password,
                             repository_name, image_tag):
        self.requires_at_least("4.1.0")

        url = self._routes.model_version_export(model_id, model_version_id)

        request = {
            "registryUrl": registry_host,
            "username": registry_username,
            "password": registry_password,
            "repository": repository_name,
            "tag": image_tag
        }

        response = self.request_manager.post(url, json=request)
        return response.json()


    def model_version_sagemaker_export(self, model_id, model_version_id, registry_host,
                             registry_username, registry_password,
                             repository_name, image_tag):
        self.requires_at_least("4.2.0")

        url = self._routes.model_version_sagemaker_export(model_id, model_version_id)

        request = {
            "registryUrl": registry_host,
            "username": registry_username,
            "password": registry_password,
            "repository": repository_name,
            "tag": image_tag
        }

        response = self.request_manager.post(url, json=request)
        return response.json()

    def model_version_export_status(self, model_export_id):
        self.requires_at_least("4.1.0")

        url =  self._routes.model_version_export_status(model_export_id)
        return self._get(url)

    def model_version_export_logs(self, model_export_id):
        self.requires_at_least("4.1.0")

        url =  self._routes.model_version_export_logs(model_export_id)
        return self._get(url)

    # Hardware Tier Functions
    def hardware_tiers_list(self):
        url = self._routes.hardware_tiers_list(self._project_id)
        return self._get(url)

    def process_log(self, log):
        """
        spool out and replay entire log using bs4 to strip the HTML tags
            - html.parser since it's batteries included
        """
        for line in log.splitlines():
            if line and line != ".":
                text = BeautifulSoup(line, "html.parser").text

                if "text-danger" in line:
                    self.log.warning(text)
                else:
                    self.log.info(text)

    # Validation methods
    def _useable_environments_list(self):
        self.log.debug(f"Getting list of useable environment")
        useable_environment_list_url = self._routes.useable_environments_list(self._project_id)
        return self.request_manager.get(useable_environment_list_url).json()['environments']

    def _validate_environment_id(self, environment_id):
        self.log.debug(f"Validating environment id: {environment_id}")
        for environment in self._useable_environments_list():
            if environment_id == environment['id']:
                return True
        raise EnvironmentNotFoundException(f"{environment_id} environment not found")

    def _validate_hardware_tier_id(self, hardware_tier_id):
        self.log.debug(f"Validating hardware tier id: {hardware_tier_id}")
        for hardware_tier in self.hardware_tiers_list():
            if hardware_tier_id == hardware_tier['hardwareTier']['id']:
                return True
        raise HardwareTierNotFoundException(f"{hardware_tier_id} hardware tier Id not found")

    def _validate_hardware_tier_name(self, hardware_tier_name):
        self.log.debug(f"Validating hardware tier id: {hardware_tier_name}")
        for hardware_tier in self.hardware_tiers_list():
            if hardware_tier_name == hardware_tier['hardwareTier']['name']:
                return True
        raise HardwareTierNotFoundException(f"{hardware_tier_name} hardware tier name not found")

    def _validate_commit_id(self, commit_id):
        self.log.debug(f"Validating commit id: {commit_id}")
        for commit in self.commits_list():
            if commit_id == commit:
                return True
        raise CommitNotFoundException(f"{commit_id} commit Id not found")

    # Helper methods
    def _get(self, url):
        return self.request_manager.get(url).json()

    def _put_file(self, url, file):
        return self.request_manager.put(url, data=file)

    @staticmethod
    def _validate_blob_key(key):
        regex = re.compile("^\\w{40,40}$")
        if not regex.match(key):
            raise Exception(("Blob key should be 40 alphanumeric characters. "
                             "Perhaps you passed a file path on accident? "
                             "If you have a file path and want to get the "
                             "file, use files_list to get the blob key."))

    @staticmethod
    def _validate_information_data_type(info: dict):
        accepted_units = {'GiB': True, 'MB': True}

        try:
            unit = info["unit"]
            value = info["value"]
            accepted_units[unit]
        except KeyError:
            raise Exception(
                f"Information value is formatted incorrectly." +
                f" Allowed units: {', '.join(accepted_units.keys())}" +
                " Example: { 'unit': 'GiB', 'value': 5 }"
            )

    def requires_at_least(self, at_least_version):
        if at_least_version > self._version:
            raise Exception("You need at least version {} but your deployment \
                            seems to be running {}".format(
                at_least_version, self._version))

    # Workaround to get project ID which is needed for some model functions
    @property
    @functools.lru_cache()
    def _project_id(self):
        url = self._routes.find_project_by_owner_name_and_project_name_url()
        key = "id"
        response = self._get(url)
        if key in response.keys():
            return response[key]

    # This will fetch app_id of app in current project
    @property
    def _app_id(self):
        url = self._routes.app_list(self._project_id)
        response = self._get(url)
        if len(response) != 0:
            app = response[0]
        else:
            return None
        key = "id"
        if key in app.keys():
            app_id = app[key]
        else:
            app_id = None
        return app_id

    _csrf_no_check_header = {'Csrf-Token': 'nocheck'}
