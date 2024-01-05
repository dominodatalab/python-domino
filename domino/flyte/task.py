import json
from enum import Enum
from typing import Any, Dict, Optional, Type, List
from datetime import timedelta
from dataclasses import dataclass, asdict
from flytekit.configuration import SerializationSettings
from flytekit.core.base_task import PythonTask, TaskMetadata
from flytekit.core.interface import Interface
from flytekit.extend.backend.base_agent import AsyncAgentExecutorMixin

@dataclass
class GitRef(object):
    type: str
    value: Optional[str] = None

# Must inherit from str for json serialization to work
class EnvironmentRevisionType(str, Enum):
    ActiveRevision = "ActiveRevision"
    LatestRevision = "LatestRevision"
    SomeRevision = "SomeRevision"
    RestrictedRevision = "RestrictedRevision"


@dataclass 
class EnvironmentRevisionSpec(object):
    EnvironmentRevisionType: EnvironmentRevisionType
    EnvironmentRevisionId: Optional[str] = None

    def __post_init__(self):
        if self.EnvironmentRevisionType == EnvironmentRevisionType.SomeRevision and not self.EnvironmentRevisionId:
            raise ValueError(f"EnvironmentRevisionId must be specified when using type {self.EnvironmentRevisionType}")

    def __str__(self):
        if self.EnvironmentRevisionType == EnvironmentRevisionType.SomeRevision:
            return f"{self.EnvironmentRevisionType.value}({self.EnvironmentRevisionId})"
        else:
            return self.EnvironmentRevisionType.value


# Must inherit from str for json serialization to work
class ComputeClusterType(str, Enum):
    Dask = "Dask"
    Spark = "Spark"
    Ray = "Ray"
    MPI = "MPI"


@dataclass
class ClusterProperties(object):
    ClusterType: ComputeClusterType
    ComputeEnvironmentId: str
    WorkerHardareTierId: str
    WorkerCount: int
    WorkerStorageGiB: Optional[float] = None
    MaxWorkerCount: Optional[int] = None
    ComputeEnvironmentRevisionSpec: Optional[EnvironmentRevisionSpec] = None
    MasterHardwareTierId: Optional[str] = None
    ExtraConfigs: Optional[Dict[str, str]] = None


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
    MainRepoGitRef: Optional[GitRef] = None
    HardwareTierId: Optional[str] = None
    EnvironmentId: Optional[str] = None
    EnvironmentRevisionSpec: Optional[EnvironmentRevisionSpec] = None
    ComputeClusterProperties: Optional[ClusterProperties] = None
    VolumeSizeGiB: Optional[float] = None
    ExternalVolumeMounts: Optional[List[str]] = None


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
            "jobConfig": json.dumps(asdict(self._task_config))
        }
