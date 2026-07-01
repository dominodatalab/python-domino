"""
Tests for the scheduled jobs API.
Unit tests only — no live Domino deployment required.
"""

import pytest

from domino import Domino

MOCK_PROJECT_ID = "aabbccddeeff001122334454"
MOCK_USER_ID = "aabbccddeeff001122334456"
MOCK_SCHEDULED_JOB_ID = "aabbccddeeff001122334458"

MOCK_CRON_SCHEDULE = {
    "cronString": "0 0 9 ? * MON",
    "isCustom": True,
    "humanReadableCronString": "At 09:00 on Monday",
}

MOCK_DATA_CONFIG = {
    "snapshotDatasetsOnCompletion": False,
    "snapshotNetAppVolumesOnCompletion": False,
}

MOCK_SCHEDULED_JOB = {
    "id": MOCK_SCHEDULED_JOB_ID,
    "created": "2024-01-01T00:00:00Z",
    "projectId": MOCK_PROJECT_ID,
    "title": "Weekly Report",
    "command": "report.py",
    "schedule": MOCK_CRON_SCHEDULE,
    "timezoneId": "America/New_York",
    "isPaused": False,
    "allowConcurrentExecution": False,
    "hardwareTierIdentifier": "small-k8s",
    "hardwareTierName": "Small",
    "environmentRevisionSpec": "ActiveRevision",
    "scheduledByUserId": MOCK_USER_ID,
    "scheduledByUserName": "anyuser",
    "notifyOnCompleteEmailAddresses": [],
    "dataConfig": MOCK_DATA_CONFIG,
}


MOCK_HARDWARE_TIER_ID = "small-k8s"

MOCK_HARDWARE_TIERS = [
    {"hardwareTier": {"id": MOCK_HARDWARE_TIER_ID, "name": "Small"}},
]

MOCK_ENVIRONMENT_ID = "envid123456789012345678"

MOCK_USEABLE_ENVIRONMENTS = [
    {"id": MOCK_ENVIRONMENT_ID, "name": "Default Environment"},
]


@pytest.fixture
def base_mocks(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID},
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/users",
        json=[{"id": MOCK_USER_ID, "userName": "anyuser", "email": "anyuser@example.com"}],
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/hardwareTiers",
        json=MOCK_HARDWARE_TIERS,
    )
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/useableEnvironments",
        json={"environments": MOCK_USEABLE_ENVIRONMENTS},
    )
    yield


def test_scheduled_jobs_list(requests_mock, dummy_hostname, base_mocks):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/scheduledjobs",
        json=[MOCK_SCHEDULED_JOB],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.scheduled_jobs_list()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == MOCK_SCHEDULED_JOB_ID


def test_scheduled_jobs_list_with_explicit_project_id(requests_mock, dummy_hostname, base_mocks):
    other_project_id = "bbccddeeff0011223344aabb"
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{other_project_id}/scheduledjobs",
        json=[],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.scheduled_jobs_list(project_id=other_project_id)
    assert result == []


def test_scheduled_job_get(requests_mock, dummy_hostname, base_mocks):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/scheduledjobs/{MOCK_SCHEDULED_JOB_ID}",
        json=MOCK_SCHEDULED_JOB,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.scheduled_job_get(MOCK_SCHEDULED_JOB_ID)
    assert result["id"] == MOCK_SCHEDULED_JOB_ID
    assert result["title"] == "Weekly Report"
    assert result["command"] == "report.py"


def test_scheduled_job_create(requests_mock, dummy_hostname, base_mocks):
    requests_mock.post(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/scheduledjobs",
        json=MOCK_SCHEDULED_JOB,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.scheduled_job_create(
        title="Weekly Report",
        command="report.py",
        cron_string="0 0 9 ? * MON",
        timezone_id="America/New_York",
        hardware_tier_identifier="small-k8s",
    )
    assert result["id"] == MOCK_SCHEDULED_JOB_ID
    assert result["title"] == "Weekly Report"

    # Verify the request body contained required fields
    last_request = requests_mock.last_request
    body = last_request.json()
    assert body["title"] == "Weekly Report"
    assert body["command"] == "report.py"
    assert body["schedule"]["cronString"] == "0 0 9 ? * MON"
    assert body["schedule"]["isCustom"] is True
    assert body["timezoneId"] == "America/New_York"
    assert body["hardwareTierIdentifier"] == "small-k8s"
    assert body["environmentRevisionSpec"] == "ActiveRevision"
    assert body["scheduledByUserId"] == MOCK_USER_ID
    assert body["isPaused"] is False
    assert body["allowConcurrentExecution"] is False
    assert body["notifyOnCompleteEmailAddresses"] == []


def test_scheduled_job_create_with_optional_fields(requests_mock, dummy_hostname, base_mocks):
    requests_mock.post(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/scheduledjobs",
        json=MOCK_SCHEDULED_JOB,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.scheduled_job_create(
        title="Weekly Report",
        command="report.py",
        cron_string="0 0 9 ? * MON",
        timezone_id="America/New_York",
        hardware_tier_identifier="small-k8s",
        environment_revision_spec="LatestRevision",
        is_paused=True,
        allow_concurrent_execution=True,
        is_custom_schedule=False,
        notify_on_complete_email_addresses=["user@example.com"],
        capacity_type="spot",
        override_environment_id="envid123456789012345678",
        external_volume_mounts=["volid123456789012345678"],
        snapshot_datasets_on_completion=True,
        snapshot_net_app_volumes_on_completion=False,
    )

    body = requests_mock.last_request.json()
    assert body["environmentRevisionSpec"] == "LatestRevision"
    assert body["isPaused"] is True
    assert body["allowConcurrentExecution"] is True
    assert body["schedule"]["isCustom"] is False
    assert body["notifyOnCompleteEmailAddresses"] == ["user@example.com"]
    assert body["capacityType"] == "spot"
    assert body["overrideEnvironmentId"] == "envid123456789012345678"
    assert body["externalVolumeMounts"] == ["volid123456789012345678"]
    assert body["snapshotDatasetsOnCompletion"] is True
    assert body["snapshotNetAppVolumesOnCompletion"] is False


def test_scheduled_job_update(requests_mock, dummy_hostname, base_mocks):
    updated = {**MOCK_SCHEDULED_JOB, "title": "Updated Report", "isPaused": True}
    requests_mock.put(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/scheduledjobs/{MOCK_SCHEDULED_JOB_ID}",
        json=updated,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.scheduled_job_update(
        scheduled_job_id=MOCK_SCHEDULED_JOB_ID,
        title="Updated Report",
        command="report.py",
        cron_string="0 0 9 ? * MON",
        timezone_id="America/New_York",
        hardware_tier_identifier="small-k8s",
        is_paused=True,
    )
    assert result["title"] == "Updated Report"
    assert result["isPaused"] is True

    body = requests_mock.last_request.json()
    assert body["title"] == "Updated Report"
    assert body["isPaused"] is True
    assert body["scheduledByUserId"] == MOCK_USER_ID


def test_scheduled_job_delete(requests_mock, dummy_hostname, base_mocks):
    requests_mock.delete(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/scheduledjobs/{MOCK_SCHEDULED_JOB_ID}",
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    response = d.scheduled_job_delete(MOCK_SCHEDULED_JOB_ID)
    assert response.status_code == 200
