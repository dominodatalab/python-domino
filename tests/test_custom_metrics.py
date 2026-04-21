"""
Unit tests for the custom metrics client.
Tests target _CustomMetricsClient (hand-rolled) directly, since
_CustomMetricsClientGen wraps OpenAPI-generated validation that requires
integration-level setup. Our Bug 6 fix lives in _CustomMetricsClient.
All tests use requests_mock — no live Domino deployment required.
"""

import pytest

from domino import Domino
from domino._custom_metrics import _CustomMetricsClient

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_MODEL_MONITORING_ID = "aabbccddeeff001122334461"


@pytest.fixture
def base_mocks(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID},
    )
    yield


@pytest.fixture
def hand_rolled_client(requests_mock, dummy_hostname, base_mocks):
    """Returns _CustomMetricsClient (hand-rolled) bound to a Domino instance."""
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    return _CustomMetricsClient(d, d._routes)


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_trigger_alert_payload_without_condition(
    requests_mock, dummy_hostname, hand_rolled_client
):
    alert_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricAlerts/v1", status_code=200
    )
    hand_rolled_client.trigger_alert(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
    )
    body = alert_mock.last_request.json()
    assert body["modelMonitoringId"] == MOCK_MODEL_MONITORING_ID
    assert body["metric"] == "accuracy"
    assert body["value"] == 0.95
    assert "targetRange" not in body


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_trigger_alert_payload_with_condition(
    requests_mock, dummy_hostname, hand_rolled_client
):
    alert_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricAlerts/v1", status_code=200
    )
    hand_rolled_client.trigger_alert(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
        condition="GREATER_THAN",
        lower_limit=0.8,
        upper_limit=1.0,
    )
    body = alert_mock.last_request.json()
    assert body["targetRange"]["condition"] == "GREATER_THAN"
    assert body["targetRange"]["lowerLimit"] == 0.8
    assert body["targetRange"]["upperLimit"] == 1.0


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_trigger_alert_payload_with_condition_no_limits(
    requests_mock, dummy_hostname, hand_rolled_client
):
    alert_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricAlerts/v1", status_code=200
    )
    hand_rolled_client.trigger_alert(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
        condition="LESS_THAN",
    )
    body = alert_mock.last_request.json()
    assert body["targetRange"]["condition"] == "LESS_THAN"
    assert "lowerLimit" not in body["targetRange"]
    assert "upperLimit" not in body["targetRange"]


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_trigger_alert_includes_description_when_provided(
    requests_mock, dummy_hostname, hand_rolled_client
):
    alert_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricAlerts/v1", status_code=200
    )
    hand_rolled_client.trigger_alert(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
        description="Accuracy dropped below threshold",
    )
    body = alert_mock.last_request.json()
    assert body["description"] == "Accuracy dropped below threshold"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_trigger_alert_omits_description_when_not_provided(
    requests_mock, dummy_hostname, hand_rolled_client
):
    alert_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricAlerts/v1", status_code=200
    )
    hand_rolled_client.trigger_alert(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
    )
    body = alert_mock.last_request.json()
    assert "description" not in body


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_log_metric_sends_correct_payload(
    requests_mock, dummy_hostname, hand_rolled_client
):
    log_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricValues/v1", status_code=200
    )
    hand_rolled_client.log_metric(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
        timestamp="2024-01-01T00:00:00Z",
    )
    body = log_mock.last_request.json()
    assert "newMetricValues" in body
    item = body["newMetricValues"][0]
    assert item["modelMonitoringId"] == MOCK_MODEL_MONITORING_ID
    assert item["metric"] == "accuracy"
    assert item["value"] == 0.95


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_log_metric_includes_tags_when_provided(
    requests_mock, dummy_hostname, hand_rolled_client
):
    log_mock = requests_mock.post(
        f"{dummy_hostname}/api/metricValues/v1", status_code=200
    )
    hand_rolled_client.log_metric(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        value=0.95,
        timestamp="2024-01-01T00:00:00Z",
        tags={"env": "production"},
    )
    body = log_mock.last_request.json()
    item = body["newMetricValues"][0]
    assert "tags" in item


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_read_metrics_returns_dict(requests_mock, dummy_hostname, hand_rolled_client):
    requests_mock.get(
        f"{dummy_hostname}/api/metricValues/v1/{MOCK_MODEL_MONITORING_ID}/accuracy",
        json={"values": [{"value": 0.95, "timestamp": "2024-01-01T00:00:00Z"}]},
    )
    result = hand_rolled_client.read_metrics(
        model_monitoring_id=MOCK_MODEL_MONITORING_ID,
        metric="accuracy",
        start_timestamp="2024-01-01T00:00:00Z",
        end_timestamp="2024-12-31T23:59:59Z",
    )
    assert "values" in result
