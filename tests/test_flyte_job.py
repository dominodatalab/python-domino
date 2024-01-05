from domino.flyte.task import *

from dataclasses import asdict

def test_job_config_serialization():
    job_config = DominoJobConfig(
        Username="user",
        ProjectName="project",
        ApiKey="apiKey", 
        Command="command", 
        Title="title", 
        CommitId="commitId", 
        MainRepoGitRef=GitRef("branch", "main"), 
        HardwareTierId="hardwareTierId", 
        EnvironmentId="environmentId", 
        EnvironmentRevisionSpec=EnvironmentRevisionSpec(EnvironmentRevisionType.LatestRevision), 
        ComputeClusterProperties=ClusterProperties(
            ClusterType=ComputeClusterType.Dask, 
            ComputeEnvironmentId="computeEnvId", 
            WorkerHardareTierId="workerHardwareTierId",
            WorkerCount=1, 
            WorkerStorageGiB=3.4, 
            MaxWorkerCount=4,
            ComputeEnvironmentRevisionSpec=EnvironmentRevisionSpec(EnvironmentRevisionType.ActiveRevision),
            MasterHardwareTierId="masterHardwareTierId",
            ExtraConfigs=None
        ), 
        VolumeSizeGib=1.2, 
        ExternalVolumeMounts=None
    )

    config_str = json.dumps(asdict(job_config))

    loaded_job_config = DominoJobConfig(**json.loads(config_str))

    assert job_config == loaded_job_config