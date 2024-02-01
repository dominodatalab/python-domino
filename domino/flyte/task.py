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


    def isResolved(self):
        return self.ComputeEnvironmentRevisionSpec and (self.MasterHardwareTierId or self.ClusterType == ComputeClusterType.MPI)


    def toJson(self) -> dict:
        return {
            "clusterType": self.ClusterType,
            "computeEnvironmentId": self.ComputeEnvironmentId,
            "computeEnvironmentRevisionSpec": self.ComputeEnvironmentRevisionSpec,  # Should always be resolved before toJson is called
            "masterHardwareTierId": self.MasterHardwareTierId,
            "workerCount": self.WorkerCount,
            "maxWorkerCount": self.MaxWorkerCount,
            "workerHardwareTierId": self.WorkerHardareTierId,
            "workerStorage": { "value": self.WorkerStorageGiB, "unit": "GiB"} if self.WorkerStorageGiB else None,
            "extraConfigs": self.ExtraConfigs,
        }


# Names here are lowercase to make serialization easier
@dataclass
class DatasetSnapshot(object):
    datasetId: str
    snapshotVersion: int


@dataclass
class DominoJobConfig(object):
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
    DatasetSnapshots: Optional[List[DatasetSnapshot]] = None
    ExternalVolumeMountIds: Optional[List[str]] = None


    def isResolved(self):
        return (
            self.CommitId and
            self.HardwareTierId and
            self.EnvironmentId and
            self.EnvironmentRevisionSpec and
            (not self.ComputeClusterProperties or self.ComputeClusterProperties.isResolved()) and
            self.VolumeSizeGiB and
            self.DatasetSnapshots and
            self.ExternalVolumeMountIds
        )
        

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
            "datasetSnapshots": self.DatasetSnapshots,
            "externalVolumeMountIds": self.ExternalVolumeMountIds,
            "volumeSizeGiB": self.VolumeSizeGiB,
            "title": self.Title,
            "mainRepoGitRef": asdict(self.MainRepoGitRef) if self.MainRepoGitRef else None,
            "computeClusterProperties": self.ComputeClusterProperties.toJson() if self.ComputeClusterProperties else None,
            "inputInterfaceBase64": None,
            "inputOutputInterfaceBase64": None,
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

        super().__init__(
            name=name,
            task_type="domino_job",
            task_config=resolved_job_config,
            interface=Interface(inputs=inputs, outputs=outputs),
            inputs=inputs,
            outputs=outputs,
            metadata=TaskMetadata(retries=0, timeout=timedelta(hours=3)),
            **kwargs,
        )
        # Interface class passed into task constructor doesn't have to_flyte_idl() so can't seem to get the correct base64 vals before instantiating the task.
        # The flyte init container (which downloads inputs) and flyte sidecar (which uploads outputs) require these
        #   base64 string encodings of the input/output interfaces as args to their container startup commands.
        if inputs or outputs:
            flyte_idl_interface = self._interface.to_flyte_idl()
            if inputs:
                serialized_input_interface = flyte_idl_interface.inputs.SerializeToString()  # just inputs  -- for init/downloader
                self.task_config["inputInterfaceBase64"] = base64.b64encode(serialized_input_interface).decode("ascii")
            if outputs:
                serialized_input_output_interface = flyte_idl_interface.SerializeToString()  # inputs and outputs -- for sidecar/uploader
                self.task_config["inputOutputInterfaceBase64"] = base64.b64encode(serialized_input_output_interface).decode("ascii")


    def _resolve_job_properties(self, domino_job_config: DominoJobConfig) -> Dict[str, Any]:
        if domino_job_config.isResolved():
            return domino_job_config.toJson()
        
        logger.info("Retrieving default properties for job")
        # TODO: Can we make this work outside of runs?
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

        return resolved_job_config            
        

    # This is used to surface job config values necessary for the agent to send requests
    def get_custom(self, settings: SerializationSettings) -> Dict[str, Any]:
        return self._task_config
