import json
import os
import requests
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


@dataclass
class ResolvedDominoJobConfig(object):
    ### Auth ###
    Username: str
    ProjectName: str
    ApiKey: str
    ### Job Config ###
    Command: str
    Title: Optional[str] = None
    CommitId: str
    MainRepoGitRef: Optional[GitRef] = None
    HardwareTierId: str
    EnvironmentId: str
    EnvironmentRevisionSpec: EnvironmentRevisionSpec
    ComputeClusterProperties: Optional[ClusterProperties] = None
    VolumeSizeGiB: float
    ExternalVolumeMounts: List[str]

class DominoJobTask(AsyncAgentExecutorMixin, PythonTask[DominoJobConfig]):
    def __init__(
        self,
        name: str,
        domino_job_config: DominoJobConfig,
        inputs: Optional[Dict[str, Type]] = None,
        outputs: Optional[Dict[str, Type]] = None,
        **kwargs,
    ):       

        resolved_job_config = self._resolve_job_properties(domino_job_config)

        super().__init__(
            name=name,
            task_type="domino_job",
            task_config=resolved_job_config,
            interface=Interface(),
            inputs=inputs,
            outputs=outputs,
            metadata=TaskMetadata(retries=0, timeout=timedelta(hours=3)),
            **kwargs,
        )


    def _resolve_job_properties(self, domino_job_config: DominoJobConfig) -> ResolvedDominoJobConfig:
        if (
            domino_job_config.CommitId is None or
            domino_job_config.HardwareTierId is None or
            domino_job_config.EnvironmentId is None or
            domino_job_config.EnvironmentRevisionSpec is None or
            domino_job_config.VolumeSizeGiB is None or
            domino_job_config.ExternalVolumeMounts is None
            # TODO: Compute cluster validation
        ):
            url = f"{os.environ["DOMINO_API_PROXY"]}/v4/jobs/{domino_job_config.OwnerName}/{domino_job_config.ProjectName}/resolveJobDefaults"
            response = requests.post(url, json=json.dumps(asdict(domino_job_config)))
            response.raise_for_status()
            
            return DominoJobConfig(**json.loads(response.json()))
        else:
            return domino_job_config
        

    # This is used to surface ResolvedDominoJobConfig values necessary to send the request    
    def get_custom(self, settings: SerializationSettings) -> Dict[str, Any]:
        return {
            "jobConfig": json.dumps(asdict(self._task_config))
        }
