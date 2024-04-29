import functools
import json
import logging
import os
from packaging import version
import re
import time
from typing import List, Optional, Tuple
import warnings

import polling2
import requests
from bs4 import BeautifulSoup

from domino import exceptions, helpers, datasets
from domino._version import __version__
from domino.authentication import get_auth_by_type
from domino.domino_enums import BillingTagSettingMode, BudgetLabel, BudgetType, ProjectVisibility
from domino.constants import (
    CLUSTER_TYPE_MIN_SUPPORT,
    DOMINO_HOST_KEY_NAME,
    DOMINO_LOG_LEVEL_KEY_NAME,
    MINIMUM_EXTERNAL_VOLUME_MOUNTS_SUPPORT_DOMINO_VERSION,
    MINIMUM_ON_DEMAND_SPARK_CLUSTER_SUPPORT_DOMINO_VERSION,
    MINIMUM_SUPPORTED_DOMINO_VERSION,
)
from domino.http_request_manager import _HttpRequestManager
from domino.routes import _Routes
from domino._custom_metrics import _CustomMetricsClientBase, _CustomMetricsClientGen, _CustomMetricsClient


class Domino:
    def __init__(
        self, project, api_key=None, host=None, domino_token_file=None, auth_token=None, api_proxy=None,
    ):

        self._configure_logging()

        _host = host or os.getenv(DOMINO_HOST_KEY_NAME)
        assert _host, (
            "Host must be supplied as a parameter or through the "
            f"{DOMINO_HOST_KEY_NAME} environment variable."
        )
        host = helpers.clean_host_url(_host)

        try:
            self._owner_username, self._project_name = project.split("/")
            self._routes = _Routes(host, self._owner_username, self._project_name)
        except ValueError:
            self._logger.error(
                f"Project {project} must be given in the form username/projectname"
            )
            raise

        # This call sets self.request_manager
        self.authenticate(api_key, auth_token, domino_token_file, api_proxy)

        # Get version
        self._version = self.deployment_version().get("version")
        assert self.requires_at_least(MINIMUM_SUPPORTED_DOMINO_VERSION)

        self._logger.debug(
            f"Domino deployment {host} is running version {self._version}"
        )

        # Check version compatibility
        if not helpers.is_version_compatible(self._version):
            error_message = (
                f"Domino version: {self._version} is not compatible with "
                f"python-domino version: {__version__}"
            )
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
        logging_level = logging.getLevelName(
            os.getenv(DOMINO_LOG_LEVEL_KEY_NAME, "INFO").upper()
        )
        logging.basicConfig(level=logging_level)
        self._logger = logging.getLogger(__name__)

    def authenticate(self, api_key=None, auth_token=None, domino_token_file=None, api_proxy=None):
        """
        Method to authenticate the request manager. An existing domino client object can
        use this with a new token if the existing credentials expire.
        """
        self.request_manager = _HttpRequestManager(
            get_auth_by_type(
                api_key=api_key,
                auth_token=auth_token,
                domino_token_file=domino_token_file,
                api_proxy=api_proxy,
            )
        )

    def commits_list(self):
        url = self._routes.commits_list()
        return self._get(url)

    def runs_list(self):
        url = self._routes.runs_list()
        return self._get(url)

    def runs_start(
        self,
        command,
        isDirect=False,
        commitId=None,
        title=None,
        tier=None,
        publishApiEndpoint=None,
    ):

        url = self._routes.runs_start()

        request = {
            "command": command,
            "isDirect": isDirect,
            "commitId": commitId,
            "title": title,
            "tier": tier,
            "publishApiEndpoint": publishApiEndpoint,
        }
        try:
            response = self.request_manager.post(url, json=request)
            return response.json()
        except exceptions.ReloginRequiredException:
            self._logger.info(
                f" You need to log in to the Domino UI to start the run. Please do it at {self._routes.host}/relogin?redirectPath=/"
            )

    def runs_start_blocking(
        self,
        command,
        isDirect=False,
        commitId=None,
        title=None,
        tier=None,
        publishApiEndpoint=None,
        poll_freq=5,
        max_poll_time=6000,
        retry_count=5,
    ):
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
        run_response = self.runs_start(
            command, isDirect, commitId, title, tier, publishApiEndpoint
        )
        run_id = run_response["runId"]

        poll_start = time.time()
        current_retry_count = 0
        while True:
            try:
                run_info = self.get_run_info(run_id)
                if run_info is None:
                    raise exceptions.RunNotFoundException(
                        f"Tried to access nonexistent run id {run_id}"
                    )
                current_retry_count = 0
            except (
                requests.exceptions.RequestException,
                exceptions.RunNotFoundException,
            ) as e:
                current_retry_count += 1
                self.log.warning(f"Failed to get run info for runId: {run_id} : {e}")
                if current_retry_count > retry_count:
                    raise Exception(
                        f"Cannot get run info, max retry {retry_count} exceeded"
                    ) from None
                else:
                    self.log.info(
                        f"Retrying ({current_retry_count}/{retry_count}) getting run info ..."
                    )
                    time.sleep(poll_freq)
                    continue

            elapsed_time = time.time() - poll_start

            if elapsed_time >= max_poll_time:
                raise Exception(f"Run exceeded maximum time of {max_poll_time} seconds")

            output_commit_id = run_info.get("outputCommitId")
            if not output_commit_id:
                time.sleep(poll_freq)
                continue

            # once task has finished running check to see if it was successful
            else:
                stdout_msg = self.get_run_log(runId=run_id, includeSetupLog=False)

                if run_info["status"] != "Succeeded":
                    self.process_log(stdout_msg)
                    raise exceptions.RunFailedException(
                        f"Remote run {run_id} finished but did not succeed."
                    )

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
        for run_info in self.runs_list()["data"]:
            if run_info["id"] == run_id:
                return run_info

    def runs_stdout(self, runId):
        """
        Get std out emitted by a particular run.

        parameters
        ----------
        runId : string
                the id associated with the run.
        """

        html_start_tags = (
            "<pre style='white-space: pre-wrap; white-space: -moz-pre-wrap; white-space: -pre-wrap; "
            "white-space: -o-pre-wrap; word-wrap: break-word; word-wrap: break-all;'>"
        )
        html_end_tags = "</pre>$"
        span_regex = re.compile("<?span.*?>")
        returns = "'\\n'\n"

        url = self._routes.runs_stdout(runId)
        raw_stdout = self._get(url)["stdout"]

        stdout = (
            re.sub(html_end_tags, "", re.sub(span_regex, "", raw_stdout))
            .replace(html_start_tags, "")
            .replace(returns, "\n")
        )

        return stdout

    def job_start(
        self,
        command: str,
        commit_id: Optional[str] = None,
        hardware_tier_id: Optional[str] = None,
        hardware_tier_name: Optional[str] = None,
        environment_id: Optional[str] = None,
        on_demand_spark_cluster_properties: Optional[dict] = None,
        compute_cluster_properties: Optional[dict] = None,
        external_volume_mounts: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> dict:
        """
        Starts a Domino Job via V4 API
        :param command:                             string
                                                    Command to execute in Job
                                                    >> domino.job_start(command="main.py arg1 arg2")
        :param commit_id:                           string (Optional)
                                                    The commitId to launch from. If not provided, will launch
                                                    from latest commit.
        :param hardware_tier_id:                    string (Optional)
                                                    The hardware tier ID to launch job in. If not provided
                                                    it will use the default hardware tier for the project
        :param hardware_tier_name:                  string (Optional)
                                                    This field is deprecated. Please use hardware_tier_id.
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
                                                    to launch a job that uses compute cluster instead of
                                                    the deprecated on_demand_spark_cluster_properties field. If
                                                    on_demand_spark_cluster_properties and compute_cluster_properties
                                                    are both present, on_demand_spark_cluster_properties will be ignored.

                                                    compute_cluster_properties contains the following fields:
                                                    {
                                                        "clusterType": <string, one of "Ray", "Spark", "Dask", "MPI">,
                                                        "computeEnvironmentId": <string, The environment ID for the cluster's nodes>,
                                                        "computeEnvironmentRevisionSpec": <one of "ActiveRevision", "LatestRevision",
                                                        {"revisionId":"<environment_revision_id>"} (optional)>,
                                                        "masterHardwareTierId": <string, the Hardware tier ID for the cluster's master node
                                                        (required unless clusterType is MPI)>,
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
        :param title                                string (Optional)
                                                    Title for the Job
        :return: Returns created Job details (number, id etc)
        """

        def validate_on_demand_spark_cluster_properties(max_execution_slot_per_user):
            self.log.debug(
                f"Validating spark cluster properties: {on_demand_spark_cluster_properties}"
            )
            validations = {
                "executorCount": lambda ec: validate_spark_executor_count(
                    int(ec), max_execution_slot_per_user
                ),
                "computeEnvironmentId": lambda com_env_id: self._validate_environment_id(
                    com_env_id
                ),
                "executorHardwareTierId": lambda exec_hwd_tier_id: self._validate_hardware_tier_id(
                    exec_hwd_tier_id
                ),
                "masterHardwareTierId": lambda master_hwd_tier_id: self._validate_hardware_tier_id(
                    master_hwd_tier_id
                ),
                "executorStorageMB": lambda exec_storage_mb: True,
            }
            if "computeEnvironmentId" not in on_demand_spark_cluster_properties:
                raise exceptions.MissingRequiredFieldException(
                    "Mandatory field computeEnvironmentId not passed in spark properties"
                )
            for k, v in on_demand_spark_cluster_properties.items():
                if not validations.get(k, lambda x: False)(v):
                    raise exceptions.MalformedInputException(
                        f"Invalid spark property {k}:{v} found"
                    )

        def validate_spark_executor_count(executor_count, max_executor_count):
            if executor_count <= max_executor_count:
                return True
            else:
                raise exceptions.MalformedInputException(
                    f"executor count: {executor_count} exceeding max executor count: {max_executor_count}"
                )

        def get_default_spark_settings():
            self.log.debug("Getting default spark settings")
            default_spark_setting_url = self._routes.default_spark_setting(
                self.project_id
            )
            return self.request_manager.get(default_spark_setting_url).json()

        def validate_is_on_demand_spark_supported():
            if not helpers.is_on_demand_spark_cluster_supported(self._version):
                raise exceptions.OnDemandSparkClusterNotSupportedException(
                    f"Your domino deployment version {self._version} does not support on demand spark cluster. "
                    f"Minimum support version {MINIMUM_ON_DEMAND_SPARK_CLUSTER_SUPPORT_DOMINO_VERSION}"
                )

        def validate_distributed_compute_cluster_properties():
            if not helpers.is_compute_cluster_properties_supported(self._version):
                raise exceptions.UnsupportedFieldException(
                    f"'compute_cluster_properties' is not supported in Domino {self._version}."
                )

            required_keys = [
                "clusterType",
                "computeEnvironmentId",
                "masterHardwareTierId",
                "workerHardwareTierId",
                "workerCount",
            ]
            required_key_overrides = {("masterHardwareTierId", "MPI"): False}

            for key in required_keys:
                key_required = required_key_overrides.get(
                    (key, compute_cluster_properties["clusterType"]), True
                )

                if key_required and (key not in compute_cluster_properties):
                    raise exceptions.MissingRequiredFieldException(
                        f"{key} is required in compute_cluster_properties"
                    )

            if not helpers.is_cluster_type_supported(
                self._version, compute_cluster_properties["clusterType"]
            ):
                supported_types = [
                    ct
                    for ct, min_version in CLUSTER_TYPE_MIN_SUPPORT
                    if helpers.is_cluster_type_supported(self._version, ct)
                ]
                supported_types_str = ", ".join(supported_types)
                raise exceptions.MalformedInputException(
                    f"Domino {self._version} does not support cluster type {compute_cluster_properties['clusterType']}."
                    + f" This version of Domino supports the following cluster types: {supported_types_str}"
                )

            def throw_if_information_invalid(key: str, info: dict) -> bool:
                try:
                    self._validate_information_data_type(info)
                except Exception as e:
                    raise exceptions.MalformedInputException(
                        f"{key} in compute_cluster_properties failed validation: {e}"
                    )

            if "workerStorage" in compute_cluster_properties:
                throw_if_information_invalid(
                    "workerStorage", compute_cluster_properties["workerStorage"]
                )

            if compute_cluster_properties["workerCount"] < 1:
                raise exceptions.MalformedInputException(
                    "compute_cluster_properties.workerCount must be greater than 0"
                )

            if (
                "maxWorkerCount" in compute_cluster_properties
                and not helpers.is_comute_cluster_autoscaling_supported(self._version)
            ):
                raise exceptions.UnsupportedFieldException(
                    f"'maxWorkerCount' is not supported in Domino {self._version}."
                )

            if "masterHardwareTierId" in compute_cluster_properties:
                self._validate_hardware_tier_id(compute_cluster_properties["masterHardwareTierId"])

            self._validate_hardware_tier_id(compute_cluster_properties["workerHardwareTierId"])

        def validate_is_external_volume_mounts_supported():
            if not helpers.is_external_volume_mounts_supported(self._version):
                raise exceptions.ExternalVolumeMountsNotSupportedException(
                    f"Your domino deployment version {self._version} does not support external volume mounts. "
                    f"Minimum support version {MINIMUM_EXTERNAL_VOLUME_MOUNTS_SUPPORT_DOMINO_VERSION}"
                )

        spark_cluster_properties = None
        validated_compute_cluster_properties = None

        if commit_id is not None:
            self._validate_commit_id(commit_id)
        if hardware_tier_id is not None:
            self._validate_hardware_tier_id(hardware_tier_id)
        if hardware_tier_name is not None:
            self._validate_hardware_tier_name(hardware_tier_name)
        if environment_id is not None:
            self._validate_environment_id(environment_id)
        if external_volume_mounts is not None:
            validate_is_external_volume_mounts_supported()
        if compute_cluster_properties is not None:
            validate_distributed_compute_cluster_properties()

            validated_compute_cluster_properties = compute_cluster_properties.copy()

            if "masterHardwareTierId" in compute_cluster_properties:
                validated_compute_cluster_properties["masterHardwareTierId"] = {
                    "value": compute_cluster_properties["masterHardwareTierId"]
                }

            validated_compute_cluster_properties["workerHardwareTierId"] = {
                "value": compute_cluster_properties["workerHardwareTierId"]
            }

        elif on_demand_spark_cluster_properties is not None:
            validate_is_on_demand_spark_supported()
            default_spark_setting = get_default_spark_settings()
            max_execution_slot = default_spark_setting["maximumExecutionSlotsPerUser"]
            default_executor_hardware_tier = default_spark_setting[
                "executorHardwareTierId"
            ]
            default_master_hardware_tier = default_spark_setting["masterHardwareTierId"]
            validate_on_demand_spark_cluster_properties(max_execution_slot)
            executor_hardware_tier_id = on_demand_spark_cluster_properties.get(
                "executorHardwareTierId", default_executor_hardware_tier
            )
            master_hardware_tier_id = on_demand_spark_cluster_properties.get(
                "masterHardwareTierId", default_master_hardware_tier
            )
            executor_count = int(
                on_demand_spark_cluster_properties.get("executorCount", 1)
            )
            compute_environment_id = on_demand_spark_cluster_properties.get(
                "computeEnvironmentId"
            )
            executor_storage = int(
                on_demand_spark_cluster_properties.get("executorStorageMB", 0)
            )
            spark_cluster_properties = {
                "computeEnvironmentId": compute_environment_id,
                "executorCount": executor_count,
                "executorHardwareTierId": executor_hardware_tier_id,
                "executorStorageMB": executor_storage,
                "masterHardwareTierId": master_hardware_tier_id,
            }

        resolved_hardware_tier_id = (
            hardware_tier_id or self.get_hardware_tier_id_from_name(hardware_tier_name)
        )
        url = self._routes.job_start()
        payload = {
            "projectId": self.project_id,
            "commandToRun": command,
            "commitId": commit_id,
            "overrideHardwareTierId": resolved_hardware_tier_id,
            "onDemandSparkClusterProperties": spark_cluster_properties,
            "computeClusterProperties": validated_compute_cluster_properties,
            "environmentId": environment_id,
            "externalVolumeMounts": external_volume_mounts,
            "title": title,
        }
        try:
            response = self.request_manager.post(url, json=payload)
            return response.json()
        except exceptions.ReloginRequiredException:
            self._logger.info(
                f" You need to log in to the Domino UI to start the job. Please do it at {self._routes.host}/relogin?redirectPath=/"
            )

    def job_stop(self, job_id: str, commit_results: bool = True):
        """
        Stops the Job with given job_id
        :param job_id: The job identifier
        :param commit_results: Boolean representing to commit results to file
        """
        url = self._routes.job_stop()
        request = {
            "projectId": self.project_id,
            "jobId": job_id,
            "commitResults": commit_results,
        }
        response = self.request_manager.post(url, json=request)
        return response

    def job_status(self, job_id: str) -> dict:
        """
        Gets the status of job with given job_id
        :param job_id: The job identifier
        :return: The details
        """
        return self.request_manager.get(self._routes.job_status(job_id)).json()

    def job_runtime_execution_details(self, job_id: str) -> dict:
        """
        Gets the runtime execution details of job with given job_id
        :param job_id: The job identifier
        :return: The details
        """
        return self.request_manager.get(
            self._routes.job_runtime_execution_details(job_id)
        ).json()

    def job_start_blocking(
        self,
        poll_freq: int = 5,
        max_poll_time: int = 6000,
        ignore_exceptions: Tuple = (requests.exceptions.RequestException,),
        **kwargs,
    ) -> dict:
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
            self.log.info(
                f"Polling Job: {job_identifier} status is completed: {status['statuses']['isCompleted']}"
            )
            if status["statuses"]["executionStatus"] == "Failed":
                raise exceptions.RunFailedException(
                    f"Run Status Failed for run: {job_identifier}"
                )
            return status

        job = self.job_start(**kwargs)
        job_id = job["id"]
        job_status = polling2.poll(
            target=lambda: get_job_status(job_id),
            check_success=lambda status: status["statuses"]["isCompleted"],
            ignore_exceptions=ignore_exceptions,
            timeout=max_poll_time,
            step=poll_freq,
            log_error=self.log.level,
        )
        stdout_msg = self.get_run_log(runId=job_id, includeSetupLog=False)
        self.process_log(stdout_msg)
        return job_status

    def files_list(self, commitId, path="/"):
        url = self._routes.files_list(commitId, path)
        return self._get(url)

    def files_upload(self, path, file):
        if not path.startswith("/"):
            path = "/" + path
        url = self._routes.files_upload(path)
        return self._put_file(url, file)

    def blobs_get(self, key):
        """
        Deprecated. Use blobs_get_v2(path, commit_id, project_id) instead
        :param key: blob key
        :return: blob content
        """
        message = "blobs_get is deprecated and will soon be removed. Please migrate to blobs_get_v2 and adjust the " \
                  "input parameters accordingly "
        warnings.warn(message, DeprecationWarning)
        self._validate_blob_key(key)
        url = self._routes.blobs_get(key)
        return self.request_manager.get_raw(url)

    def blobs_get_v2(self, path, commit_id, project_id):
        self._validate_blob_path(path)
        url = self._routes.blobs_get_v2(path, commit_id, project_id)
        return self.request_manager.get_raw(url)

    def fork_project(self, target_name):
        url = self._routes.fork_project(self.project_id)
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
            "bindingDefinition": {"file": file, "function": function},
        }

        response = self.request_manager.post(url, json=request)
        return response

    def deployment_version(self):
        url = self._routes.deployment_version()
        return self._get(url)

    def project_create_v4(
        self,
        project_name: str,
        owner_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        description: Optional[str] = "",
        collaborators: Optional[list] = None,
        tags: Optional[list] = None,
        billing_tag: Optional[str] = None,
        visibility: Optional[ProjectVisibility] = ProjectVisibility.PUBLIC,
    ):
        owner = (
            owner_id if owner_id else self.get_user_id(owner_username) if owner_username
            else self.get_user_id(self._owner_username)
        )
        data = {
            "name": project_name,
            "visibility": visibility.value,
            "ownerId": owner,
            "description": description,
            "collaborators": collaborators if collaborators is not None else [],
            "tags": {"tagNames": tags if tags is not None else []},
        }

        if billing_tag:
            data.update({"billingTag": {"tag": billing_tag}})

        url = self._routes.project_v4()
        payload = json.dumps(data)
        response = self.request_manager.post(url, data=payload, headers={'Content-Type': 'application/json'})
        return response.json()

    def project_create(self, project_name, owner_username=None):
        url = self._routes.project_create()
        data = {"projectName": project_name, "ownerOverrideUsername": owner_username}
        response = self.request_manager.post(
            url, data=data, headers=self._csrf_no_check_header
        )
        return response

    def project_archive(self, project_name):
        """Delete the project with the given name"""
        all_owned_projects = self.projects_list(show_completed=True)
        for p in all_owned_projects:
            if p["name"] == project_name:
                url = self._routes.project_v4(project_id=p["id"])
                self.request_manager.delete(url)
                break
        else:
            raise exceptions.ProjectNotFoundException(project_name)

    def projects_list(self, relationship="Owned", show_completed=False):
        url = self._routes.projects_list()

        valid_relationships = ["Owned", "Collaborating", "Suggesting", "Popular"]
        if relationship not in valid_relationships:
            raise ValueError(
                f"relationship must be one of {valid_relationships}: {relationship}"
            )

        query = {
            "relationship": relationship,
            "showCompleted": str(show_completed).lower(),
        }
        response = self.request_manager.get(url, params=query)
        return response.json()

    def tags_list(self, project_id=None):
        project_id = project_id if project_id else self.project_id
        url = self._routes.project_v4(project_id)
        return self._get(url)["tags"]

    def tag_details(self, tag_id):
        url = self._routes.tag_details(tag_id)
        return self._get(url)

    def tags_add(self, tags: list, project_id=None):
        project_id = project_id if project_id else self.project_id
        js_body = {"tagNames": tags}
        url = self._routes.tags_add(project_id)
        response = self.request_manager.post(url, json=js_body)
        return response

    def tag_get_id(self, tag_name, project_id=None):
        tags = self.tags_list(project_id)
        for tag in tags:
            if tag_name == tag["name"]:
                return tag["id"]
        logging.warning(f"tag with name {tag_name} not found for this project")
        return

    def tags_remove(self, tag_name, project_id=None):
        project_id = project_id if project_id else self.project_id
        tag_id = self.tag_get_id(tag_name, project_id)

        if tag_id:
            url = self._routes.tags_remove(project_id, tag_id)
            response = self.request_manager.delete(url)
            return response
        return

    def collaborators_get(self):
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
            if username_or_email in (user.get("userName"), user.get("email")):
                user_id = user["id"]
                break
        return user_id

    def collaborators_add(self, username_or_email, message=""):
        user_id = self.get_user_id(username_or_email)

        if user_id is None:
            raise exceptions.UserNotFoundException(
                f"Could not add collaborator matching {username_or_email}"
            )

        url = self._routes.collaborators_add(self.project_id)
        request = {"collaboratorId": user_id, "projectRole": "Contributor"}

        response = self.request_manager.post(url, json=request)
        return response

    def collaborators_remove(self, username_or_email):
        user_id = self.get_user_id(username_or_email)

        if user_id is None:
            raise exceptions.UserNotFoundException(
                f"Could not remove collaborator matching {username_or_email}"
            )

        url = self._routes.collaborators_remove(self.project_id, user_id)

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
        request = {"hardwareTierId": hardwareTierId}
        response = self.request_manager.post(url, json=request)
        return response

    def app_unpublish(self):
        app_id = self._app_id
        if app_id is None:
            return
        status = self.__app_get_status(app_id)
        self.log.debug(f"App {app_id} status={status}")
        if status and status != "Stopped" and status != "Failed":
            url = self._routes.app_stop(app_id)
            response = self.request_manager.post(url)
            return response

    def __app_get_status(self, id) -> Optional[str]:
        app_id = self._app_id
        if app_id is None:
            return None
        url = self._routes.app_get(app_id)
        response = self.request_manager.get(url).json()
        return response.get("status", None)

    def __app_create(self, name: str = "", hardware_tier_id: str = None) -> str:
        """
        Private method to create app

        :param name: Optional field to set title of app
        :param hardware_tier_id: Optional field to override hardware tier
        :return: Id of newly created App (Un-Published)
        """
        url = self._routes.app_create()
        request_payload = {
            "modelProductType": "APP",
            "projectId": self.project_id,
            "name": name,
            "owner": "",
            "created": time.time_ns(),
            "lastUpdated": time.time_ns(),
            "status": "",
            "media": [],
            "openUrl": "",
            "tags": [],
            "stats": {"usageCount": 0},
            "appExtension": {"appType": ""},
            "id": "000000000000000000000000",
            "permissionsData": {
                "visibility": "GRANT_BASED",
                "accessRequestStatuses": {},
                "pendingInvitations": [],
                "discoverable": True,
                "appAccessStatus": "ALLOWED",
            },
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
        url = self._routes.environments_list()
        return self._get(url)

    # Model Manager functions
    def models_list(self):
        url = self._routes.models_list()
        return self._get(url)

    def model_publish(
        self, file, function, environment_id, name, description, files_to_exclude=None
    ):
        if files_to_exclude is None:
            files_to_exclude = []
        url = self._routes.model_publish()

        request = {
            "name": name,
            "description": description,
            "projectId": self.project_id,
            "file": file,
            "function": function,
            "excludeFiles": files_to_exclude,
            "environmentId": environment_id,
        }

        response = self.request_manager.post(url, json=request)
        return response.json()

    def model_versions_get(self, model_id):
        url = self._routes.model_versions_get(model_id)
        return self._get(url)

    def model_version_publish(
        self,
        model_id,
        file,
        function,
        environment_id,
        description,
        files_to_exclude=None,
    ):
        if files_to_exclude is None:
            files_to_exclude = []
        url = self._routes.model_version_publish(model_id)

        request = {
            "description": description,
            "projectId": self.project_id,
            "file": file,
            "function": function,
            "excludeFiles": files_to_exclude,
            "environmentId": environment_id,
        }

        response = self.request_manager.post(url, json=request)
        return response.json()

    # Dataset Functions
    def datasets_list(self, project_id=None):
        url = self._routes.datasets_list(project_id)
        return self._get(url)

    def datasets_ids(self, project_id) -> list:
        dataset_list = self.datasets_list(project_id)
        dataset_ids = [dataset_id["datasetId"] for dataset_id in dataset_list]
        return dataset_ids

    def datasets_names(self, project_id) -> list:
        dataset_list = self.datasets_list(project_id)
        dataset_names = [dataset_id["datasetName"] for dataset_id in dataset_list]
        return dataset_names

    def datasets_create(self, dataset_name, dataset_description):
        if dataset_name in self.datasets_names(self.project_id):
            raise exceptions.DatasetExistsException("Dataset Name must be Unique")

        url = self._routes.datasets_create()
        request = {
            "datasetName": dataset_name,
            "description": dataset_description,
            "projectId": self.project_id,
        }
        response = self.request_manager.post(url, json=request)
        return response.json()

    def datasets_details(self, dataset_id):
        url = self._routes.datasets_details(dataset_id)
        return self._get(url)

    def datasets_update_details(
        self, dataset_id, dataset_name=None, dataset_description=None
    ):
        url = self._routes.datasets_details(dataset_id)
        request = {}
        if dataset_name:
            if dataset_name in self.datasets_names(self.project_id):
                raise exceptions.DatasetExistsException("Dataset Name must be Unique")
            else:
                request.update({"datasetName": dataset_name})
        if dataset_description:
            request.update({"description": dataset_description})

        self.request_manager.patch(url, json=request)

        return self._get(url)

    def _dataset_remove(self, dataset_id):
        if dataset_id in self.datasets_ids(self.project_id):
            raise exceptions.DatasetNotFoundException(
                f"Dataset with id {dataset_id} does not exist"
            )
        url = self._routes.datasets_details(dataset_id)
        response = self.request_manager.delete(url)
        return response

    def datasets_remove(self, dataset_ids: list):
        for dataset_id in dataset_ids:
            url = self._routes.datasets_details(dataset_id)
            self.request_manager.delete(url)

    def datasets_upload_files(
        self,
        dataset_id: str,
        local_path_to_file_or_directory: str,
        file_upload_setting: str = None,
        max_workers: int = None,
        target_chunk_size: int = None,
        target_relative_path: str = None
    ) -> str:
        """Upload file to dataset with multithreaded support.

        Note: in the case of a KeyboardInterrupt, it may take a few seconds for all the threads to stop and for the
        upload session to be properly cancelled.

        Args:
            dataset_id: id of dataset whose rw snapshot the file will be uploaded to
            local_path_to_file_or_directory: path to file or directory in local machine
            file_upload_setting: setting to resolve naming conflict, one of Rename, Overwrite, or Ignore (default).
                - Rename: renames the conflicting file being uploaded by appending "_n" where n is an integer.
                - Overwrite: overrides the existing conflicting files.
                - Ignore (default): skips the upload for any conflicting file.
            max_workers: max amount of threads (default: 10)
            target_chunk_size: max chunk size for multipart upload (default: 8MB)
            target_relative_path: path in the dataset to upload the file or directory to
        Returns local path to uploaded file
        """
        if file_upload_setting is None or file_upload_setting == "Ignore":
            text = "Ignore setting selected - any file with naming conflict will not be uploaded."
        elif file_upload_setting == "Overwrite":
            text = "Overwrite setting selected - note that any existing file with naming conflict " \
                   "will be overridden."
        elif file_upload_setting == "Rename":
            text = "Rename setting selected - note that naming conflicts will be resolved by appending " \
                   "an increasing integer at the end of the uploaded files. In case of a directory with " \
                   "numerous conflicts, this will cause severe file proliferation."
        else:
            raise ValueError(f"input file_upload_setting {file_upload_setting} not allowed. Please use "
                             f"`Overwrite`, `Rename`, or `Ignore` only.")
        self.log.warning(text)

        with datasets.Uploader(
            csrf_no_check_header=self._csrf_no_check_header,
            dataset_id=dataset_id,
            local_path_to_file_or_directory=local_path_to_file_or_directory,
            log=self.log,
            request_manager=self.request_manager,
            routes=self._routes,

            file_upload_setting=file_upload_setting,
            max_workers=max_workers,
            target_chunk_size=target_chunk_size,
            target_relative_path=target_relative_path
        ) as uploader:
            path = uploader.upload()
            self.log.info(f"Uploading chunks for file or directory `{path}` to dataset {dataset_id} completed. "
                          f"Now attempting to end upload session.")
            return path

    def model_version_export(
        self,
        model_id,
        model_version_id,
        registry_host,
        registry_username,
        registry_password,
        repository_name,
        image_tag,
    ):
        self.requires_at_least("4.1.0")

        url = self._routes.model_version_export(model_id, model_version_id)

        request = {
            "registryUrl": registry_host,
            "username": registry_username,
            "password": registry_password,
            "repository": repository_name,
            "tag": image_tag,
        }

        response = self.request_manager.post(url, json=request)
        return response.json()

    def model_version_sagemaker_export(
        self,
        model_id,
        model_version_id,
        registry_host,
        registry_username,
        registry_password,
        repository_name,
        image_tag,
    ):
        self.requires_at_least("4.2.0")

        url = self._routes.model_version_sagemaker_export(model_id, model_version_id)

        request = {
            "registryUrl": registry_host,
            "username": registry_username,
            "password": registry_password,
            "repository": repository_name,
            "tag": image_tag,
        }

        response = self.request_manager.post(url, json=request)
        return response.json()

    def model_version_export_status(self, model_export_id):
        self.requires_at_least("4.1.0")

        url = self._routes.model_version_export_status(model_export_id)
        return self._get(url)

    def model_version_export_logs(self, model_export_id):
        self.requires_at_least("4.1.0")

        url = self._routes.model_version_export_logs(model_export_id)
        return self._get(url)

    # Hardware Tier Functions
    def hardware_tiers_list(self):
        url = self._routes.hardware_tiers_list(self.project_id)
        return self._get(url)

    def get_hardware_tier_id_from_name(self, hardware_tier_name: str):
        for hardware_tier in self.hardware_tiers_list():
            if hardware_tier_name == hardware_tier["hardwareTier"]["name"]:
                return hardware_tier["hardwareTier"]["id"]
        return None

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

    def budget_defaults_list(self) -> list:
        """
        Get a list of the available default budgets with the assigned (if any) limits
        Requires Admin permission

        :return: Returns a list of default budgets with details
        """
        url = self._routes.budgets_default()
        return self.request_manager.get(url).json()

    def budget_defaults_update(self, budget_label: BudgetLabel, budget_limit: float) -> dict:
        """
        Update default budgets limits (or quota) by BudgetLabel
        Requires Admin permission

        :param budget_label: label of budget to be updated ex: `BillingTag`, `Organization`
        :param budget_limit: new budget quota to assign to default label

        :return: Returns the updated budget with the newly assigned limit.
        """
        url = self._routes.budgets_default(budget_label.value)
        updated_budget = {"budgetLabel": budget_label.value, "budgetType": "Default", "limit": budget_limit,
                          "window": "monthly"}
        data = json.dumps(updated_budget)
        return self.request_manager.put(url, data=data, headers={"Content-Type": "application/json"}).json()

    def budget_overrides_list(self):
        """
        Get a list of the available budgets overrides with the assigned limits.
        Requires Admin permission

        :return: Returns a list of budgets overrides with details
        """
        url = self._routes.budget_overrides()
        return self.request_manager.get(url).json()

    def budget_override_create(self, budget_label: BudgetLabel, budget_id: str, budget_limit: float) -> dict:
        """
        Create Budget overrides based on BudgetLabels, ie BillingTags, Organization, or Projects
        the object id is used as budget ids
        Requires Admin roles

        :param budget_label: label of budget to be updated
        :param budget_id: id of project or organization to be used as new budget override id.
        :param budget_limit: budget quota to assign to override

        :return: Returns the newly created budget override
        """
        url = self._routes.budget_overrides()
        new_budget: dict = self._generate_budget(budget_label, budget_id, budget_limit)
        data = json.dumps(new_budget)
        return self.request_manager.post(url, data=data, headers={"Content-Type": "application/json"}).json()

    def budget_override_update(self, budget_label: BudgetLabel, budget_id: str, budget_limit: float) -> dict:
        """
        Update Budget overrides based on BudgetLabel and budget id
        Requires Admin roles

        :param budget_label: label of budget to be updated
        :param budget_id: id of budget override to be updated.
        :param budget_limit: new budget quota to assign to override

        :return: Returns the updated budget override
        """
        url = self._routes.budget_overrides(budget_id)
        new_budget: dict = self._generate_budget(budget_label, budget_id, budget_limit)
        data = json.dumps(new_budget)
        return self.request_manager.put(url, data=data, headers={"Content-Type": "application/json"}).json()

    def budget_override_delete(self, budget_id: str) -> list:
        """
        Delete an existing budget override
        Requires Admin roles

        :param budget_id: id of budget override to be deleted.

        :return: Returns list of messages confirming the budget override deletion
        """
        url = self._routes.budget_overrides(budget_id)
        return self.request_manager.delete(url).json()

    def budget_alerts_settings(self) -> dict:
        """
        Get the current budget alerts settings
        Requires Admin permission

        :return: Returns the current budget alert setting
        """
        url = self._routes.budget_settings()
        return self.request_manager.get(url).json()

    def budget_alerts_settings_update(
        self,
        alerts_enabled: Optional[bool] = None,
        notify_org_owner: Optional[bool] = None
    ) -> dict:
        """
        Update the current budget alerts settings to enable/disable budget notifications
        and whether to notify org owners on projects notifications
        Requires Admin permission

        :param alerts_enabled: whether to enable or disable notifications.
        :param notify_org_owner: whether to notify organizations owners on projects reaching threshold.

        :return: Returns the updated budget alert setting
        """
        current_settings = self.budget_alerts_settings()

        optional_fields = {
            "alertsEnabled": alerts_enabled,
            "notifyOrgOwner": notify_org_owner
        }

        updated_settings = self._update_if_set(current_settings, optional_fields)

        payload = json.dumps(updated_settings)
        url = self._routes.budget_settings()
        return self.request_manager.put(url, data=payload).json()

    def budget_alerts_targets_update(self, targets: dict[BudgetLabel, list]) -> dict:
        """
        Update the current budget alerts settings with additional email targets per budget label
        Requires Admin permission

        :param targets: dictionary of budget labels and list of email addresses

        :return: Returns the updated budget alert setting
        """

        budget_settings = self.budget_alerts_settings()

        current_targets = budget_settings["alertTargets"]

        updated_targets = []

        for target in current_targets:
            if target["label"] in targets:
                updated_targets.append({"label": target["label"], "emails": targets[target["label"]]})
            else:
                updated_targets.append(target)

        budget_settings["alertTargets"] = updated_targets

        payload = json.dumps(budget_settings)
        url = self._routes.budget_settings()
        return self.request_manager.put(url, data=payload).json()

    def billing_tags_list_active(self) -> dict:
        """
        Get a list of active billing tags
        Requires Admin permission

        :return: Returns a dictionary containing the list active billing tags
        """
        self.requires_at_least("5.11.0")
        url = self._routes.billing_tags()
        return self.request_manager.get(url).json()

    def billing_tags_create(self, tags_list: list) -> dict:
        """
        Create a list of active billing tags
        Requires Admin permission

        :param tags_list: list of billing tags names to be created

        :return: Returns a dictionary containing the list newly created billing tags
        """
        self.requires_at_least("5.11.0")
        url = self._routes.billing_tags()
        payload = json.dumps({"billingTags": tags_list})
        return self.request_manager.post(url, data=payload, headers={"Content-Type": "application/json"}).json()

    def active_billing_tag_by_name(self, name: str) -> dict:
        """
        Get detailed info on active or archived billing tag
        Requires Admin permission

        :param name: name of existing billing tag

        :return: Returns a dictionary containing the list newly created billing tags
        """
        url = self._routes.billing_tags(name)
        return self.request_manager.get(url).json()

    def billing_tag_archive(self, name: str) -> dict:
        """
        Archive an active billing tag
        Requires Admin permission

        :param name: name of existing billing tag to archive

        :return: Returns a dictionary containing the updated billing tag
        """
        url = self._routes.billing_tags(name)
        return self.request_manager.delete(url).json()

    def billing_tag_settings(self) -> dict:
        """
        Get the current billing tag settings
        Requires Admin permission

        :return: Returns the current billing tag settings
        """
        url = self._routes.billing_tags_settings()
        return self.request_manager.get(url).json()

    def billing_tag_settings_mode(self) -> dict:
        """
        Get the current billing tag settings mode
        Requires Admin permission

        :return: Returns the current billing tag settings mode
        """
        url = self._routes.billing_tags_settings(mode_only=True)
        return self.request_manager.get(url).json()

    def billing_tag_settings_mode_update(self, mode: BillingTagSettingMode) -> dict[str, BillingTagSettingMode]:
        """
        Update the current billing tag settings mode
        Requires Admin permission

        :param mode: new mode to set the billing tag settings (see BillingTagSettingMode)

        :return: Returns the updated billing tag settings mode
        """
        url = self._routes.billing_tags_settings(mode_only=True)
        payload = json.dumps({"mode": mode.value})
        return self.request_manager.put(url, data=payload, headers={"Content-Type": "application/json"}).json()

    def project_billing_tag(self, project_id: Optional[str] = None) -> Optional[dict]:
        """
        Get a billing tag assigned to a particular project by project id
        Requires Admin permission

        :param project_id: id of the project to find assigned billing tag

        :return: Returns the billing tag if assigned or None
        """
        url = self._routes.project_billing_tag(project_id if project_id else self.project_id)
        return self.request_manager.get(url).json()

    def project_billing_tag_update(self, billing_tag: str, project_id: Optional[str] = None) -> dict:
        """
        Update project's billing tag with new billing tag.
        Requires Admin permission

        :param billing_tag: billing tag to assign to a project
        :param project_id: id of the project to assign a billing tag

        :return: Returns the project details including the new billing tag
        """
        url = self._routes.project_billing_tag(project_id if project_id else self.project_id)
        data = {
            "tag": billing_tag
        }
        return self.request_manager.post(url, data=json.dumps(data)).json()

    def project_billing_tag_reset(self, project_id: Optional[str] = None) -> dict:
        """
        Remove a billing tag from a specified project
        Requires Admin permission

        :param project_id: id of the project to reset billing tag field

        :return: Returns the project details
        """
        url = self._routes.project_billing_tag(project_id if project_id else self.project_id)
        return self.request_manager.delete(url).json()

    def projects_by_billing_tag(
        self,
        billing_tag: Optional[str] = None,
        offset: Optional[int] = 0,
        page_size: Optional[int] = 10,
        name_filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        missing_tag_only: bool = False,
    ) -> dict:
        """
        Remove a billing tag from a specified project
        Requires Admin permission

        :param billing_tag: billing tag string to filter projects by
        :param offset: The index of the start of the page, where checkpointProjectId is index 0.
                        If the offset is negative the project it points to will be the end of the page.
        :param page_size: The number of record to return per page.
        :param name_filter: matches projects by name substring
        :param sort_by: (Optional) field to sort the projects on
        :param sort_order: (Optional) Whether to sort in asc or desc order
        :param missing_tag_only: (Optional) determine whether to only return projects with missing tag

        :return: Returns a dictionary containing a page with the projects matching the query based on the page_size,
                 and to total count of projects aching the query
        """

        parameters = {
            "offset": offset,
            "pageSize": page_size,
            "missingBillingTagOnly": str(missing_tag_only).lower()
        }

        optional_params = {
            "billingTag": billing_tag,
            "nameFilter": name_filter,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        updated_params = self._update_if_set(parameters, optional_params)

        url = self._routes.projects_billing_tags()

        return self.request_manager.get(url, params=updated_params).json()

    def project_billing_tag_bulk_update(self, projects_tag: dict[str, str]) -> dict:
        """
        Update project's billing tags in bulk
        Requires Admin permission

        :param projects_tag: dictionary of project_id and billing_tags

        :return: Returns the updated projects detail summary
        """
        value_list = []
        for key, value in projects_tag.items():
            value_list.append(
                {
                    "projectId": key,
                    "billingTag": {
                        "tag": value
                    }
                }
            )

        data = {
            "projectsBillingTags": value_list
        }

        url = self._routes.projects_billing_tags()
        return self.request_manager.post(url, data=json.dumps(data)).json()

    _CUSTOM_METRICS_USE_GEN = True

    def custom_metrics_client(self) -> _CustomMetricsClientBase:
        self.requires_at_least("5.3.1")
        if self._CUSTOM_METRICS_USE_GEN:
            return _CustomMetricsClientGen(self, self._routes)
        else:
            return _CustomMetricsClient(self, self._routes)

    # Validation methods
    def _useable_environments_list(self):
        self.log.debug("Getting list of useable environment")
        useable_environment_list_url = self._routes.useable_environments_list(
            self.project_id
        )
        return self.request_manager.get(useable_environment_list_url).json()[
            "environments"
        ]

    def _validate_environment_id(self, environment_id) -> bool:
        self.log.debug(f"Validating environment id: {environment_id}")
        for environment in self._useable_environments_list():
            if environment_id == environment["id"]:
                return True
        raise exceptions.EnvironmentNotFoundException(
            f"{environment_id} environment not found"
        )

    def _validate_hardware_tier_id(self, hardware_tier_id: str) -> bool:
        self.log.debug(f"Validating hardware tier id: {hardware_tier_id}")
        for hardware_tier in self.hardware_tiers_list():
            if hardware_tier_id == hardware_tier["hardwareTier"]["id"]:
                return True
        raise exceptions.HardwareTierNotFoundException(
            f"{hardware_tier_id} hardware tier Id not found"
        )

    def _validate_hardware_tier_name(self, hardware_tier_name: str) -> bool:
        self.log.debug(f"Validating hardware tier name: {hardware_tier_name}")
        count = 0
        for hardware_tier in self.hardware_tiers_list():
            if hardware_tier_name == hardware_tier["hardwareTier"]["name"]:
                count += 1

        if count == 0:
            raise exceptions.HardwareTierNotFoundException(
                f"{hardware_tier_name} hardware tier name not found"
            )
        elif count > 1:
            raise exceptions.HardwareTierNotFoundException(
                f"{hardware_tier_name} hardware tier name has more than one match"
            )
        return True

    def _validate_commit_id(self, commit_id):
        self.log.debug(f"Validating commit id: {commit_id}")
        for commit in self.commits_list():
            if commit_id == commit:
                return True
        raise exceptions.CommitNotFoundException(f"{commit_id} commit Id not found")

    # Helper methods
    def _get(self, url):
        return self.request_manager.get(url).json()

    def _put_file(self, url, file):
        return self.request_manager.put(url, data=file)

    @staticmethod
    def _validate_blob_key(key):
        regex = re.compile("^\\w{40,40}$")
        if not regex.match(key):
            raise Exception(
                (
                    "Blob key should be 40 alphanumeric characters. "
                    "Perhaps you passed a file path on accident? "
                    "If you have a file path and want to get the "
                    "file, use files_list to get the blob key."
                )
            )

    @staticmethod
    def _validate_blob_path(path):
        """
        Helper method to validate that the path is normalized
        For example: A//B, A/B/, A/./B and A/foo/../B are not normalized/canonical, whereas A/B is.

        Args:
            path: the string of the path to check

        Return:
           None, however, it throws a MalformedInputException if the input is not normalized/canonical.
        """
        normalized_path = os.path.normpath(path)
        if path != normalized_path:
            raise exceptions.MalformedInputException(
                (
                    "Path should be normalized and cannot contain "
                    "'..' or '../'. "
                )
            )

    @staticmethod
    def _validate_information_data_type(info: dict):
        accepted_units = {"GiB": True, "MB": True}

        try:
            unit = info["unit"]
            _ = info["value"]
            accepted_units[unit]
        except KeyError:
            raise Exception(
                "Information value is formatted incorrectly."
                + f" Allowed units: {', '.join(accepted_units.keys())}"
                + " Example: { 'unit': 'GiB', 'value': 5 }"
            )

    @staticmethod
    def _generate_budget(budget_label: BudgetLabel, budget_id: str, budget_limit: float) -> dict:
        return {
            "limit": budget_limit,
            "labelId": budget_id,
            "window": "monthly",
            "budgetLabel": budget_label.value,
            "budgetType": BudgetType.OVERRIDE.value
        }

    @staticmethod
    def _update_if_set(update_dict: dict, new_dict: dict) -> dict:
        for key, value in new_dict.items():
            if value is not None:
                update_dict[key] = value
        return update_dict

    def requires_at_least(self, at_least_version):
        if version.parse(at_least_version) > version.parse(self._version):
            raise Exception(
                f"You need at least version {at_least_version} but your deployment seems to be running {self._version}"
            )
        return True

    # Workaround to get project ID which is needed for some model functions
    @property  # type: ignore # mypy incorrect error silencer
    @functools.lru_cache()
    def project_id(self):
        url = self._routes.find_project_by_owner_name_and_project_name_url()
        key = "id"
        response = self._get(url)
        if key in response.keys():
            return response[key]

    # This will fetch app_id of app in current project
    @property
    def _app_id(self):
        url = self._routes.app_list(self.project_id)
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

    _csrf_no_check_header = {"Csrf-Token": "nocheck"}
