from typing import Any, Dict, Optional, Type, Tuple
from datetime import timedelta
from dataclasses import dataclass
from flytekit.configuration import SerializationSettings
from flytekit.core.base_task import PythonTask, TaskMetadata
from flytekit.core.interface import Interface
from flytekit.extend.backend.base_agent import AsyncAgentExecutorMixin


@dataclass
class DominoJobConfig(object):
    ### Auth ###
    Username: str
    ProjectName: str
    ApiKey: str
    ### Job Config ###
    Command: str
    Title: Optional[str] = None
    CommitId: Optional[str] = None
    HardwareTierId: Optional[str] = None
    EnvironmentId: Optional[str] = None
    ComputeClusterProperties: Optional[Dict[str, str]] = None  # TODO: We probably need a better type here to pass it to the agent
    ExternalVolumeMounts: Optional[Tuple[str]] = None


class DominoJobTask(AsyncAgentExecutorMixin, PythonTask[DominoJobConfig]):
    def __init__(
        self,
        name: str,
        task_config: DominoJobConfig,
        inputs: Optional[Dict[str, Type]] = None,
        outputs: Optional[Dict[str, Type]] = None,
        **kwargs,
    ):        
        super().__init__(
            name=name,
            task_type="domino_job",
            task_config=task_config,
            interface=Interface(),
            inputs=inputs,
            outputs=outputs,
            metadata=TaskMetadata(retries=0, timeout=timedelta(hours=3)),
            **kwargs,
        )


    # This is used to surface DominoJobConfig values necessary to send the request    
    def get_custom(self, settings: SerializationSettings) -> Dict[str, Any]:
        return {
            "username": self._task_config.Username,
            "projectName": self._task_config.ProjectName,
            "apiKey": self._task_config.ApiKey,
            "command": self._task_config.Command,
            "title": self._task_config.Title,
            "commitId": self._task_config.CommitId,
            "hardwareTierId": self._task_config.HardwareTierId,
            "environmentId": self._task_config.EnvironmentId,
            "externalVolumeMounts": self.task_config.ExternalVolumeMounts,
        }