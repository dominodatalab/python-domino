import json
import os
import requests
from enum import Enum
from typing import Any, Dict, Optional, Type, List
from datetime import timedelta
from dataclasses import dataclass, asdict
import base64
from flytekit.configuration import SerializationSettings
from flytekit.core.base_task import PythonTask, TaskMetadata
from flytekit.core.interface import Interface
from flytekit.extend.backend.base_agent import AsyncAgentExecutorMixin
from flytekit.loggers import logger


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

    def toJson(self):
        if self.EnvironmentRevisionType == EnvironmentRevisionType.SomeRevision:
            return { "revisionId": self.EnvironmentRevisionId }
        else:
            return self.EnvironmentRevisionType.value


# Must inherit from str for json serialization to work
class ComputeClusterType(str, Enum):
    Dask = "Dask"
    Spark = "Spark"
    Ray = "Ray"
    MPI = "MPI"


# TODO: Define toJson here
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
class PipelineConfig:
    InputInterfaceBase64: Optional[str] = None
    InputOutputInterfaceBase64: Optional[str] = None


@dataclass
class DominoJobConfig(object):
    PipelineConfig: PipelineConfig
    ### Auth ###
    OwnerName: str
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
    ExternalVolumeMountIds: Optional[List[str]] = None

    def toJson(self) -> Dict[str, Any]:
        return {
            "ownerName": self.OwnerName,
            "projectName": self.ProjectName,
            "apiKey": self.ApiKey,
            "command": self.Command,
            "commitId": self.CommitId,
            "hardwareTierId": self.HardwareTierId,
            "environmentId": self.EnvironmentId,
            "environmentRevisionSpec": self.EnvironmentRevisionSpec.toJson() if self.EnvironmentRevisionSpec else None,
            "externalVolumeMountIds": self.ExternalVolumeMountIds,
            "volumeSizeGiB": self.VolumeSizeGiB,
            "title": self.Title,
            "mainRepoGitRef": asdict(self.MainRepoGitRef) if self.MainRepoGitRef else None,
            "computeClusterProperties": self.ComputeClusterProperties,  # TODO:
            "pipelineConfig": asdict(self.PipelineConfig),
        }


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

        task = super().__init__(
            name=name,
            task_type="domino_job",
            task_config=resolved_job_config,
            interface=Interface(inputs=inputs, outputs=outputs),
            inputs=inputs,
            outputs=outputs,
            metadata=TaskMetadata(retries=0, timeout=timedelta(hours=3)),
            **kwargs,
        )
        # the flyte init container (which downloads inputs) and flyte sidecar (which uploads outputs) require these
        # base64 string encodings of the input/output interfaces as args to their container startup commands
        # TODO: can detect "empty interfaces" here and omit the interface args so dont even create the init/sidecar containers if not needed
        serialized_input_interface = task._interface.to_flyte_idl().inputs.SerializeToString()
        serialized_input_output_interface = job._interface.to_flyte_idl().SerializeToString()
        pipelineConfig = PipelineConfig(
            InputInterfaceBase64=base64.b64encode(serialized_input_interface),
            InputOutputInterfaceBase64=base64.b64encode(serialized_input_output_interface),
        )
        domino_job_config.PipelineConfig = pipelineConfig

        return task


    def _resolve_job_properties(self, domino_job_config: DominoJobConfig) -> Dict[str, Any]:
        if (
            domino_job_config.CommitId is None or
            domino_job_config.HardwareTierId is None or
            domino_job_config.EnvironmentId is None or
            domino_job_config.EnvironmentRevisionSpec is None or
            domino_job_config.VolumeSizeGiB is None or
            domino_job_config.ExternalVolumeMountIds is None
            # TODO: Compute cluster validation
        ):
            logger.info("Retrieving default properties for job")
            url = f"{os.environ['DOMINO_API_PROXY']}/v4/jobs/{domino_job_config.OwnerName}/{domino_job_config.ProjectName}/resolveJobDefaults"
            payload = domino_job_config.toJson()

            response = requests.post(url, json=payload)
            response.raise_for_status() # TODO: Catch and sanitize error message
            
            resolved_job_config = response.json()

            # Set some values that are not resolved in the response
            resolved_job_config["ownerName"] = domino_job_config.OwnerName
            resolved_job_config["projectName"] = domino_job_config.ProjectName
            resolved_job_config["apiKey"] = domino_job_config.ApiKey
            resolved_job_config["command"] = domino_job_config.Command
            resolved_job_config["title"] = domino_job_config.Title
            resolved_job_config["pipelineConfig"] = asdict(PipelineConfig())

            return resolved_job_config            
        else:
            return domino_job_config.toJson()
        

    # This is used to surface job config values necessary for the agent to send requests
    def get_custom(self, settings: SerializationSettings) -> Dict[str, Any]:
        return self._task_config
