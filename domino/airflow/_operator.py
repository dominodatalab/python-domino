import time
from typing import Any, List, Optional

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from domino import Domino


class DominoOperator(BaseOperator):
    """
    Operator for interacting with Domino Data Lab
    via the python-domino client library w/ some
    additional functionality baked in. Follows the
    same run signature as domino.runs_start with
    some extra arguments.

    Host and API key arguments are optional and can be
    discovered via environment variable, as per the domino
    python client.

    Notes
    ------
    When combining `isDirect=True` with a command, you
    need to pass in the entire command as a single string
    in the command array.
    """

    template_fields = ("command", "title")
    ui_color = "#5188c7"

    @apply_defaults
    def __init__(
        self,
        project: str,
        command: List[str],
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        domino_token_file: Optional[str] = None,
        isDirect: bool = None,
        commitId: Optional[str] = None,
        title: Optional[str] = None,
        tier: Optional[str] = None,
        publishApiEndpoint: Optional[bool] = None,
        poll_freq: Optional[int] = 5,
        max_poll_time: Optional[int] = 6000,
        startup_delay: Optional[int] = 10,
        include_setup_log: Optional[bool] = True,
        *args,
        **kwargs
    ):
        super(DominoOperator, self).__init__(*args, **kwargs)

        self.project = project
        self._api_key = api_key
        self._host = host
        self._domino_token_file = domino_token_file
        self.command = command
        self.is_direct = isDirect
        self.commit_id = commitId
        self.title = title
        self.tier = tier
        self.publish_api_endpoint = publishApiEndpoint
        self.poll_freq = poll_freq
        self.max_poll_time = max_poll_time
        self.startup_delay = startup_delay
        self.include_setup_log = include_setup_log

        self.client: Optional[Domino] = None
        self.run_id: Optional[str] = None

    def execute(self, context: Any) -> dict:

        self.log.info("Initializing Client...")
        self.client = Domino(
            self.project, self._api_key, self._host, self._domino_token_file
        )
        self.log.info("Client Initialized for project: %s", self.project)

        if self.tier:
            self.log.info("Validating Hardware Tier")
            tier_metadata = self.client.hardware_tiers_list()

            if self.tier not in [x["hardwareTier"]["name"] for x in tier_metadata]:
                raise ValueError(
                    "Provided tier not in the list of available tiers for project."
                )

        self.log.info("Starting run.")
        if self.startup_delay:
            time.sleep(self.startup_delay)

        if self.is_direct:
            if len(self.command) > 1:
                raise ValueError(
                    "Domino API will not accept a "
                    "multipart command string this long if is_direct=True"
                )

        run_response = self.client.runs_start_blocking(
            command=self.command,
            isDirect=self.is_direct,
            commitId=self.commit_id,
            title=self.title,
            tier=self.tier,
            publishApiEndpoint=self.publish_api_endpoint,
            poll_freq=self.poll_freq,
            max_poll_time=self.max_poll_time,
        )

        self.run_id = run_response["runId"]
        log = self.client.get_run_log(self.run_id, self.include_setup_log)
        self.client.process_log(log)

        return run_response


class DominoSparkOperator(BaseOperator):
    """
    Operator for launching runs via the v4 API with
    an On-Demand Spark Cluster attached.

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
                                                On demand spark cluster properties. Following properties
                                                can be provided in spark cluster
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
    :param poll_freq: int polling frequency interval in seconds
    :param max_poll_time: int max poll time in seconds
    :param startup_delay: int (Optional) number of seconds to wait before starting the job
    """

    template_fields = ("command",)
    ui_color = "#6C50AD"

    @apply_defaults
    def __init__(
        self,
        project: str,
        command: str,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        domino_token_file: Optional[str] = None,
        poll_freq: int = 5,
        max_poll_time: int = 6000,
        startup_delay: Optional[int] = None,
        commit_id: Optional[str] = None,
        hardware_tier_name: Optional[str] = None,
        environment_id: Optional[str] = None,
        on_demand_spark_cluster_properties: Optional[dict] = None,
        *args,
        **kwargs
    ):
        super(DominoSparkOperator, self).__init__(*args, **kwargs)

        self.log.info("Initializing Client...")

        self.project = project
        self._api_key = api_key
        self._host = host
        self._domino_token_file = domino_token_file
        self.command = command
        self.commit_id = commit_id
        self.tier = hardware_tier_name
        self.poll_freq = poll_freq
        self.max_poll_time = max_poll_time
        self.startup_delay = startup_delay
        self.environment_id = environment_id
        self.spark_propertires = on_demand_spark_cluster_properties

        self.client: Optional[Domino] = None
        self.run_id: Optional[str] = None

    def execute(self, context: Any) -> dict:

        self.log.info("Initializing Client...")
        self.client = Domino(
            self.project, self._api_key, self._host, self._domino_token_file
        )
        self.log.info("Client Initialized for project: %s", self.project)

        self.log.info("Starting run.")
        if self.startup_delay:
            time.sleep(self.startup_delay)

        return self.client.job_start_blocking(
            command=self.command,
            commit_id=self.commit_id,
            hardware_tier_name=self.tier,
            environment_id=self.environment_id,
            poll_freq=self.poll_freq,
            max_poll_time=self.max_poll_time,
            on_demand_spark_cluster_properties=self.spark_propertires,
        )
