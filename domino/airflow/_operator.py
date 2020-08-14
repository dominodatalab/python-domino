import time
import logging
from typing import List, Optional, Any

from bs4 import BeautifulSoup

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

        self.log.info("Initializing Client...")
        
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

        self.client = None
        self.run_id = None

    def execute(self, context: Any) -> dict:

        self.client = Domino(self.project, self._api_key, self._host, self._domino_token_file)
        self.log.info("Client Initialized for project: %s", self.project)

        self.log.info("Starting run.")
        if self.startup_delay:
            time.sleep(self.startup_delay)

        if self.is_direct:
            if len(self.command) > 1:
                raise ValueError(
                    "Domino API will not accept a "
                    "multipart command string this long if is_direct=True"
                )

        self.client.log.setLevel(logging.ERROR)
        run_response = self.client.runs_start_blocking(
            command=self.command,
            isDirect=self.is_direct,
            commitId=self.commit_id,
            title=self.title,
            tier=self.tier,
            publishApiEndpoint=self.publish_api_endpoint,
            poll_freq=self.poll_freq,
            max_poll_time=self.max_poll_time
        )
        self.client.log.setLevel(logging.INFO)

        self.run_id = run_response["runId"]

        log = self.client.get_run_log(self.run_id, self.include_setup_log)

        # spool out and replay entire log
        for line in log.splitlines():
            if line and line != '.':
                # using bs4 to strip the HTML tags
                # html.parser since it's batteries included
                text = BeautifulSoup(line, "html.parser").text
                if "text-danger" in line:
                    self.log.warning(text)
                else:
                    self.log.info(text)

        return run_response

    def on_kill(self) -> None:
        if self.client is not None:
            self.log.info('Stopping Domino Run')
            self.client.run_stop(runId=self.run_id)
