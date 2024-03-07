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
import rich_click as click


@dataclass
class GitRef(object):
    Type: str
    Value: Optional[str] = None


    def to_json(self):
        return {
            "type": self.Type,
            "value": self.Value
        }


    @classmethod
    def from_json(cls, json: dict[str, str]):
        return cls(
            Type=json["type"],
            Value=json.get("value")
        )


# Must inherit from str for json serialization to work
class EnvironmentRevisionType(str, Enum):
    SomeRevision = "SomeRevision"
    RestrictedRevision = "RestrictedRevision"


@dataclass 
class EnvironmentRevisionSpecification(object):
    EnvironmentRevisionType: EnvironmentRevisionType
    EnvironmentRevisionId: Optional[str] = None


    def __post_init__(self):
        if self.EnvironmentRevisionType == EnvironmentRevisionType.SomeRevision and not self.EnvironmentRevisionId:
            raise ValueError(f"EnvironmentRevisionId must be specified when using type {self.EnvironmentRevisionType}")


    def to_json(self):
        if self.EnvironmentRevisionType == EnvironmentRevisionType.SomeRevision:
            return { 
                "_type": "domino.environments.api.SomeRevision",
                "revisionId": self.EnvironmentRevisionId 
            }
        else:
            return self.EnvironmentRevisionType.value


    @classmethod
    def from_json(cls, json: dict[str, str]):
        return cls(
            EnvironmentRevisionType=EnvironmentRevisionType.SomeRevision if "SomeRevision" in json["_type"] else EnvironmentRevisionType.RestrictedRevision,
            EnvironmentRevisionId=json.get("revisionId")
        )


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
    ComputeEnvironmentRevisionSpec: Optional[EnvironmentRevisionSpecification] = None
    MasterHardwareTierId: Optional[str] = None
    ExtraConfigs: Optional[Dict[str, str]] = None


    def is_resolved(self):
        return self.ComputeEnvironmentRevisionSpec and (self.MasterHardwareTierId or self.ClusterType == ComputeClusterType.MPI)


    def to_json(self) -> dict:
        return {
            "clusterType": self.ClusterType,
            "computeEnvironmentId": self.ComputeEnvironmentId,
            "computeEnvironmentRevisionSpec": self.ComputeEnvironmentRevisionSpec.to_json() if self.ComputeEnvironmentRevisionSpec else None,
            "masterHardwareTierId": { "value": self.MasterHardwareTierId } if self.MasterHardwareTierId else None,
            "workerCount": self.WorkerCount,
            "maxWorkerCount": self.MaxWorkerCount,
            "workerHardwareTierId": { "value": self.WorkerHardareTierId },
            "workerStorage": { "value": self.WorkerStorageGiB, "unit": "GiB"} if self.WorkerStorageGiB else None,
            "extraConfigs": self.ExtraConfigs,
        }
    

    @classmethod
    def from_json(cls, json: dict[str, Any]):
        return cls(
            ClusterType=json["clusterType"],
            ComputeEnvironmentId=json["computeEnvironmentId"],
            WorkerHardwareTierId=json["workerHardwareTierId"]["value"],
            WorkerCount=json["workerCount"],
            WorkerStorageGiB=json.get("workerStorageGiB"),
            MaxWorkerCount=json("maxWorkerCount"),
            ComputeEnvironmentRevisionSpec=EnvironmentRevisionSpecification.from_json(json["computeEnvironmentRevisionSpec"]),
            MasterHardwareTierId=json["masterHardwareTierId"]["value"] if json.get("masterHardwareTierId") else None,
            ExtraConfigs=json.get("extraConfigs")
        )    



@dataclass
class DatasetSnapshot(object):
    DatasetId: str
    SnapshotVersion: int
    DatasetName: Optional[str] = None  # Only used for convenience to make it easier to track datasets. Does not impact api calls


    def to_json(self) -> dict:
        return {
            "datasetId": self.DatasetId,
            "snapshotVersion": self.SnapshotVersion,
            "datasetName": self.DatasetName
        }


    @classmethod
    def from_json(cls, json: dict[str, Any]):
        return cls(
            DatasetId = json["datasetId"],
            SnapshotVersion = json["snapshotVersion"],
            DatasetName = json.get("datasetName"),
        )


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
    EnvironmentRevisionSpec: Optional[EnvironmentRevisionSpecification] = None
    ComputeClusterProperties: Optional[ClusterProperties] = None
    VolumeSizeGiB: Optional[float] = None
    DatasetSnapshots: Optional[List[DatasetSnapshot]] = None
    ExternalVolumeMountIds: Optional[List[str]] = None


    def is_resolved(self):
        return (
            self.CommitId and
            self.HardwareTierId and
            self.EnvironmentId and
            self.EnvironmentRevisionSpec and
            (not self.ComputeClusterProperties or self.ComputeClusterProperties.is_resolved()) and
            self.VolumeSizeGiB and
            self.DatasetSnapshots and
            self.ExternalVolumeMountIds != None
        )
    

    def unresolved_fields(self) -> List[str]:
        unresolved_fields = []
        if not self.CommitId: unresolved_fields.append("commitId")
        if not self.HardwareTierId: unresolved_fields.append("hardwareTierId")
        if not self.EnvironmentId: unresolved_fields.append("environmentId")
        if not self.EnvironmentRevisionSpec: unresolved_fields.append("environmentRevisionSpec")
        if self.ComputeClusterProperties and not self.ComputeClusterProperties.is_resolved(): unresolved_fields.append("computeClusterProperties")
        if not self.VolumeSizeGiB: unresolved_fields.append("volumeSizeGiB")
        if not self.DatasetSnapshots: unresolved_fields.append("datasetSnapshots")
        if self.ExternalVolumeMountIds == None: unresolved_fields.append("externalVolumeMountIds")

        return unresolved_fields
    

    def resolve_job_properties(self):
        if self.is_resolved():
            click.secho("Job properties are already fully resolved")
            return
        
        click.secho("Retrieving default properties for job")
        # TODO: Can we make this work outside of runs? Also can we modify this so we don't need owner/project in the config?
        url = f"{os.environ['DOMINO_API_PROXY']}/v4/jobs/{self.OwnerName}/{self.ProjectName}/resolveJobDefaults"
        payload = self.to_json()

        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to resolve job properties (StatusCode {response.status_code}): {response.text})")
        
        resolved_job_config = response.json()

        self.CommitId = resolved_job_config["commitId"]
        self.MainRepoGitRef = GitRef.from_json(resolved_job_config["mainRepoGitRef"]) if resolved_job_config.get("mainRepoGitRef") else None
        self.HardwareTierId = resolved_job_config["hardwareTierId"]["value"]
        self.EnvironmentId = resolved_job_config["environmentId"]
        self.EnvironmentRevisionSpec = EnvironmentRevisionSpecification.from_json(resolved_job_config["environmentRevisionSpec"])
        self.ComputeClusterProperties = ClusterProperties.from_json(resolved_job_config["computeClusterProperties"]) if resolved_job_config.get("computeClusterProperties") else None
        self.VolumeSizeGiB = resolved_job_config["volumeSizeGiB"]
        self.DatasetSnapshots = [DatasetSnapshot.from_json(snapshot_json) for snapshot_json in resolved_job_config["datasetSnapshots"]]
        self.ExternalVolumeMountIds = resolved_job_config["externalVolumeMountIds"]

        click.secho(f"Resolved job properties: {self}", fg="cyan")


    def to_json(self) -> Dict[str, Any]:
        return {
            "ownerName": self.OwnerName,
            "projectName": self.ProjectName,
            "apiKey": self.ApiKey,
            "command": self.Command,
            "commitId": self.CommitId,
            "hardwareTierId": { "value": self.HardwareTierId } if self.HardwareTierId else None,
            "environmentId": self.EnvironmentId,
            "environmentRevisionSpec": self.EnvironmentRevisionSpec.to_json() if self.EnvironmentRevisionSpec else None,
            "datasetSnapshots": [snapshot.to_json() for snapshot in self.DatasetSnapshots],
            "externalVolumeMountIds": self.ExternalVolumeMountIds,
            "volumeSizeGiB": self.VolumeSizeGiB,
            "title": self.Title,
            "mainRepoGitRef": self.MainRepoGitRef.to_json() if self.MainRepoGitRef else None,
            "computeClusterProperties": self.ComputeClusterProperties.to_json() if self.ComputeClusterProperties else None,
            "inputInterfaceBase64": None,
            "inputOutputInterfaceBase64": None,
        }


class DominoJobTask(AsyncAgentExecutorMixin, PythonTask[DominoJobConfig]):
    def __init__(
        self,
        name: str,
        domino_job_config: DominoJobConfig,
        use_latest = False,
        inputs: Optional[Dict[str, Type]] = None,
        outputs: Optional[Dict[str, Type]] = None,
        log_level: int = 20,  # 20 is info, 30 is warning, etc
        **kwargs,
    ):
        if use_latest:
            click.secho(
                "Creating task using latest values. This is not recommended, as values not explicitly defined may change between subsequent executions of this task",
                fg="yellow"
            )
            domino_job_config.resolve_job_properties()

        if not domino_job_config.is_resolved():
            unresolved_fields = domino_job_config.unresolved_fields()
            raise Exception(
                f"The following fields are not defined: {unresolved_fields}. Use DominoJobConfig.resolve_job_properties to lookup default values for these "
                "fields or run with 'use_latest' to implicitly use the latest default values for this task."
            )

        resolved_job_config = domino_job_config.to_json()

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
        

    # This is used to surface job config values necessary for the agent to send requests
    def get_custom(self, settings: SerializationSettings) -> Dict[str, Any]:
        return self._task_config
