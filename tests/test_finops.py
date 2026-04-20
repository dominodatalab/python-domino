"""
Tests for budget and billing tag (FinOps) API methods.
Unit tests at top (no live Domino deployment required).
Integration tests below (skipped unless a live deployment is reachable).
"""
import uuid
import pytest

from domino import Domino
from domino.domino_enums import BillingTagSettingMode, BudgetLabel
from domino.helpers import domino_is_reachable

MOCK_PROJECT_ID = "aabbccddeeff001122334455"
MOCK_BUDGET_ID = "aabbccddeeff001122334456"
MOCK_BUDGET_LIMIT = 0.5

MOCK_ALERT_SETTINGS = {
    "alertsEnabled": True,
    "notifyOrgOwner": False,
    "alertTargets": [
        {"label": "Project", "emails": ["old@example.com"]},
        {"label": "Organization", "emails": []},
    ],
}


@pytest.fixture
def base_mocks(requests_mock, dummy_hostname):
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "9.9.9"})
    requests_mock.get(
        f"{dummy_hostname}/v4/gateway/projects/findProjectByOwnerAndName"
        "?ownerName=anyuser&projectName=anyproject",
        json={"id": MOCK_PROJECT_ID},
    )
    yield


# ---------------------------------------------------------------------------
# Unit tests (no live Domino deployment required)
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_defaults_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/budgets/defaults",
        json=[{"budgetLabel": "Project", "limit": 1.0}],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.budget_defaults_list()
    assert isinstance(result, list)
    assert result[0]["budgetLabel"] == "Project"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_defaults_update_sends_correct_payload(requests_mock, dummy_hostname):
    update_mock = requests_mock.put(
        f"{dummy_hostname}/v4/cost/budgets/defaults/{BudgetLabel.PROJECT.value}",
        json={"budgetLabel": "Project", "limit": MOCK_BUDGET_LIMIT},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.budget_defaults_update(BudgetLabel.PROJECT, MOCK_BUDGET_LIMIT)
    body = update_mock.last_request.json()
    assert body["budgetLabel"] == "Project"
    assert body["limit"] == MOCK_BUDGET_LIMIT
    assert body["budgetType"] == "Default"
    assert body["window"] == "monthly"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_overrides_list_returns_list(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/budgets/overrides",
        json=[{"labelId": MOCK_BUDGET_ID, "limit": MOCK_BUDGET_LIMIT}],
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.budget_overrides_list()
    assert isinstance(result, list)
    assert result[0]["labelId"] == MOCK_BUDGET_ID


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_override_create_sends_correct_payload(requests_mock, dummy_hostname):
    create_mock = requests_mock.post(
        f"{dummy_hostname}/v4/cost/budgets/overrides",
        json={"labelId": MOCK_BUDGET_ID, "limit": MOCK_BUDGET_LIMIT},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.budget_override_create(BudgetLabel.PROJECT, MOCK_BUDGET_ID, MOCK_BUDGET_LIMIT)
    body = create_mock.last_request.json()
    assert body["labelId"] == MOCK_BUDGET_ID
    assert body["limit"] == MOCK_BUDGET_LIMIT
    assert body["budgetLabel"] == "Project"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_override_update_sends_put_with_correct_url(requests_mock, dummy_hostname):
    update_mock = requests_mock.put(
        f"{dummy_hostname}/v4/cost/budgets/overrides/{MOCK_BUDGET_ID}",
        json={"labelId": MOCK_BUDGET_ID, "limit": 0.9},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.budget_override_update(BudgetLabel.PROJECT, MOCK_BUDGET_ID, 0.9)
    assert update_mock.called
    assert update_mock.last_request.json()["limit"] == 0.9


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_override_delete_sends_delete(requests_mock, dummy_hostname):
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/v4/cost/budgets/overrides/{MOCK_BUDGET_ID}",
        json=["deleted"],
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.budget_override_delete(MOCK_BUDGET_ID)
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_alerts_settings_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/budgets/global/alertsSettings",
        json=MOCK_ALERT_SETTINGS,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.budget_alerts_settings()
    assert result["alertsEnabled"] is True
    assert "alertTargets" in result


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_alerts_settings_update_merges_fields(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/budgets/global/alertsSettings",
        json=MOCK_ALERT_SETTINGS,
    )
    update_mock = requests_mock.put(
        f"{dummy_hostname}/v4/cost/budgets/global/alertsSettings",
        json={**MOCK_ALERT_SETTINGS, "alertsEnabled": False},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.budget_alerts_settings_update(alerts_enabled=False)
    body = update_mock.last_request.json()
    assert body["alertsEnabled"] is False


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_budget_alerts_targets_update_updates_targets(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/budgets/global/alertsSettings",
        json=MOCK_ALERT_SETTINGS,
    )
    update_mock = requests_mock.put(
        f"{dummy_hostname}/v4/cost/budgets/global/alertsSettings",
        json=MOCK_ALERT_SETTINGS,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.budget_alerts_targets_update({"Project": ["new@example.com"]})
    body = update_mock.last_request.json()
    project_target = next(t for t in body["alertTargets"] if t["label"] == "Project")
    assert project_target["emails"] == ["new@example.com"]


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_billing_tags_list_active_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/billingtags",
        json={"billingTags": [{"tag": "env-prod", "active": True}]},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.billing_tags_list_active()
    assert "billingTags" in result
    assert result["billingTags"][0]["tag"] == "env-prod"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_billing_tags_create_sends_correct_payload(requests_mock, dummy_hostname):
    create_mock = requests_mock.post(
        f"{dummy_hostname}/v4/cost/billingtags",
        json={"billingTags": ["tag-a", "tag-b"]},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.billing_tags_create(["tag-a", "tag-b"])
    assert create_mock.called
    assert create_mock.last_request.json()["billingTags"] == ["tag-a", "tag-b"]


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_active_billing_tag_by_name_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/billingtags/tag-a",
        json={"billingTag": {"tag": "tag-a", "active": True}},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.active_billing_tag_by_name("tag-a")
    assert result["billingTag"]["tag"] == "tag-a"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_billing_tag_archive_sends_delete(requests_mock, dummy_hostname):
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/v4/cost/billingtags/tag-a",
        json={"billingTag": {"tag": "tag-a", "active": False}},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.billing_tag_archive("tag-a")
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_billing_tag_settings_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/billingtagSettings",
        json={"mode": "Optional"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.billing_tag_settings()
    assert result["mode"] == "Optional"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_billing_tag_settings_mode_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/cost/billingtagSettings/mode",
        json={"mode": "Required"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.billing_tag_settings_mode()
    assert result["mode"] == "Required"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_billing_tag_settings_mode_update_sends_correct_payload(requests_mock, dummy_hostname):
    update_mock = requests_mock.put(
        f"{dummy_hostname}/v4/cost/billingtagSettings/mode",
        json={"mode": "Required"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.billing_tag_settings_mode_update(BillingTagSettingMode.REQUIRED)
    assert update_mock.last_request.json()["mode"] == "Required"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_billing_tag_returns_tag(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/billingtag",
        json={"tag": "env-prod"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.project_billing_tag(MOCK_PROJECT_ID)
    assert result["tag"] == "env-prod"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_billing_tag_update_sends_correct_payload(requests_mock, dummy_hostname):
    update_mock = requests_mock.post(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/billingtag",
        json={"tag": "env-staging"},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.project_billing_tag_update("env-staging", MOCK_PROJECT_ID)
    assert update_mock.last_request.json()["tag"] == "env-staging"


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_billing_tag_reset_sends_delete(requests_mock, dummy_hostname):
    delete_mock = requests_mock.delete(
        f"{dummy_hostname}/v4/projects/{MOCK_PROJECT_ID}/billingtag",
        json={},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.project_billing_tag_reset(MOCK_PROJECT_ID)
    assert delete_mock.called


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_projects_by_billing_tag_returns_dict(requests_mock, dummy_hostname):
    requests_mock.get(
        f"{dummy_hostname}/v4/projects/billingtags/projects",
        json={"totalMatches": 1, "page": [{"id": MOCK_PROJECT_ID}]},
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    result = d.projects_by_billing_tag(billing_tag="env-prod")
    assert result["totalMatches"] == 1


@pytest.mark.usefixtures("clear_token_file_from_env", "base_mocks")
def test_project_billing_tag_bulk_update_sends_correct_payload(requests_mock, dummy_hostname):
    bulk_mock = requests_mock.post(
        f"{dummy_hostname}/v4/projects/billingtags/projects",
        json={"updated": 1},
        status_code=200,
    )
    d = Domino(host=dummy_hostname, project="anyuser/anyproject", api_key="whatever")
    d.project_billing_tag_bulk_update({MOCK_PROJECT_ID: "env-prod"})
    body = bulk_mock.last_request.json()
    assert len(body["projectsBillingTags"]) == 1
    assert body["projectsBillingTags"][0]["projectId"] == MOCK_PROJECT_ID
    assert body["projectsBillingTags"][0]["billingTag"]["tag"] == "env-prod"


# ---------------------------------------------------------------------------
# Integration tests (require a live Domino deployment)
# ---------------------------------------------------------------------------

def get_short_id() -> str:
    return str(uuid.uuid4())[:8]


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
@pytest.mark.parametrize("new_limit", [0.0006, 0.0037])
@pytest.mark.parametrize("budget_label", [BudgetLabel.PROJECT, BudgetLabel.ORGANIZATION, BudgetLabel.BILLINGTAG])
def test_budgets_defaults(budget_label, new_limit, default_domino_client):
    """
    Test get and update default budgets
    """
    budget_defaults = default_domino_client.budget_defaults_list()
    assert len(budget_defaults) == 3

    default_domino_client.budget_defaults_update(budget_label, new_limit)
    budget_defaults = default_domino_client.budget_defaults_list()
    for budget in budget_defaults:
        if budget["budgetLabel"] == budget_label.value:
            assert (budget["limit"] == new_limit)


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_budgets_overrides(default_domino_client):
    """
    Test creating, updating and deleting budget overrides
    """

    budget_ids = ["6626b3c64fa2ef89b5def375", "6626b3cf9106c3938a2c5f01", "6626b3d73473d4a99c2c642b"]
    budget_limit: float = 0.2048

    curr_overrides = default_domino_client.budget_overrides_list()
    overrides_count_start = len(curr_overrides)

    default_domino_client.budget_override_create(BudgetLabel.PROJECT, budget_ids[0], budget_limit)
    default_domino_client.budget_override_create(BudgetLabel.ORGANIZATION, budget_ids[1], budget_limit)
    default_domino_client.budget_override_create(BudgetLabel.BILLINGTAG, budget_ids[2], budget_limit)

    budget_overrides = default_domino_client.budget_overrides_list()

    assert len(budget_overrides) >= overrides_count_start
    for budget in budget_overrides:
        if budget["labelId"] in budget_ids:
            assert budget["limit"] == budget_limit

    new_limit = 0.1024
    default_domino_client.budget_override_update(BudgetLabel.BILLINGTAG, budget_ids[2], new_limit)

    updated_override = default_domino_client.budget_overrides_list()
    assert len(updated_override) >= 3
    for budget in updated_override:
        if budget["labelId"] == budget_ids[2]:
            assert budget["limit"] == new_limit

    for budget_id in budget_ids:
        default_domino_client.budget_override_delete(budget_id)

    overrides_reset = default_domino_client.budget_overrides_list()
    assert len(overrides_reset) == overrides_count_start


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_budgets_alerts_settings(default_domino_client):
    """
    Test creating a budget with current project, and other projects
    """
    alert_settings = default_domino_client.budget_alerts_settings()
    assert 'alertsEnabled' in alert_settings.keys()

    default_domino_client.budget_alerts_settings_update(alerts_enabled=False, notify_org_owner=False)
    update_setting_1 = default_domino_client.budget_alerts_settings()
    assert update_setting_1["alertsEnabled"] is False
    assert update_setting_1["notifyOrgOwner"] is False

    default_domino_client.budget_alerts_settings_update(alerts_enabled=True, notify_org_owner=True)
    update_setting_2 = default_domino_client.budget_alerts_settings()
    assert update_setting_2["alertsEnabled"] is True
    assert update_setting_2["notifyOrgOwner"] is True

    new_target_1 = {
        BudgetLabel.PROJECT.value: ["projectszzz@gmail.com"],
        BudgetLabel.ORGANIZATION.value: ["orgzyyy@gmail.com"],
    }

    default_domino_client.budget_alerts_targets_update(new_target_1)
    updated_settings = default_domino_client.budget_alerts_settings()
    updated_settings_t1 = updated_settings["alertTargets"]

    for new_t in updated_settings_t1:
        if new_t["label"] in new_target_1:
            assert new_t["emails"] == new_target_1[new_t["label"]]

    new_target_2 = {
        BudgetLabel.PROJECT.value: ["projectsffff@gmail.com"],
        BudgetLabel.BILLINGTAG.value: ["billing-tag@gmail.com"],
    }

    default_domino_client.budget_alerts_targets_update(new_target_2)
    updated_settings = default_domino_client.budget_alerts_settings()
    updated_settings_t2 = updated_settings["alertTargets"]

    for new_t in updated_settings_t2:
        if new_t["label"] in new_target_2:
            assert new_t["emails"] == new_target_2[new_t["label"]]


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_billing_tag_settings(default_domino_client):
    """
    Test creating a budget with current project, and other projects
    """
    billing_tag_setting = default_domino_client.billing_tag_settings()
    assert 'mode' in billing_tag_setting.keys()

    default_domino_client.billing_tag_settings_mode_update(BillingTagSettingMode.REQUIRED)
    updated_tag_setting = default_domino_client.billing_tag_settings()
    assert updated_tag_setting["mode"] == BillingTagSettingMode.REQUIRED.value
    mode = default_domino_client.billing_tag_settings_mode()
    assert mode["mode"] == BillingTagSettingMode.REQUIRED.value

    default_domino_client.billing_tag_settings_mode_update(BillingTagSettingMode.OPTIONAL)
    newer_tag_setting = default_domino_client.billing_tag_settings()
    assert newer_tag_setting["mode"] == BillingTagSettingMode.OPTIONAL.value


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_billing_tags(default_domino_client):
    """
    Test creating a budget with current project, and other projects
    """
    billing_tags = ["PYTHON-DOMINO-ACTIVE-tag-001", "PYTHON-DOMINO-ACTIVE-tag-002", "PYTHON-DOMINO-ACTIVE-tag-003"]
    new_billing_tags = default_domino_client.billing_tags_create(billing_tags)
    assert len(new_billing_tags["billingTags"]) == 3

    active_tags = default_domino_client.billing_tags_list_active()
    assert len(active_tags["billingTags"]) >= 3

    active_tag = default_domino_client.active_billing_tag_by_name(billing_tags[0])
    assert active_tag["billingTag"]["tag"] == billing_tags[0]
    assert active_tag["billingTag"]["active"] is True

    default_domino_client.billing_tag_archive(billing_tags[0])
    archive_tag = default_domino_client.active_billing_tag_by_name(billing_tags[0])
    assert archive_tag["billingTag"]["tag"] == billing_tags[0]
    assert archive_tag["billingTag"]["active"] is False


@pytest.mark.skipif(
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_projects_billing_tag(default_domino_client):
    """
    Test creating a budget with current project, and other projects
    """

    setting_mode = default_domino_client.billing_tag_settings_mode()
    if setting_mode["mode"] != BillingTagSettingMode.OPTIONAL.value:
        default_domino_client.billing_tag_settings_mode_update(BillingTagSettingMode.OPTIONAL)

    test_billing_tag = f"TestBillingTag-{get_short_id()}"
    test_billing_tag2 = f"TestBillingTag-{get_short_id()}"
    test_billing_tag3 = f"TestBillingTag-{get_short_id()}"
    default_domino_client.billing_tags_create([test_billing_tag, test_billing_tag2, test_billing_tag3])

    test_project_name = f"project-{get_short_id()}"
    test_project_name_2 = f"project-{get_short_id()}"

    bt_project = default_domino_client.project_create_v4(project_name=test_project_name, billing_tag=test_billing_tag)
    project = default_domino_client.project_create_v4(project_name=test_project_name_2)

    project_bt = default_domino_client.project_billing_tag(bt_project["id"])
    assert project_bt["tag"] == test_billing_tag

    project_bt_none = default_domino_client.project_billing_tag(project["id"])
    assert project_bt_none is None

    default_domino_client.project_billing_tag_update(test_billing_tag2, project["id"])
    project_update = default_domino_client.project_billing_tag(project["id"])
    assert project_update["tag"] == test_billing_tag2

    default_domino_client.project_billing_tag_reset(project["id"])
    project_bt_reset = default_domino_client.project_billing_tag(project["id"])
    assert project_bt_reset is None

    query_p = default_domino_client.projects_by_billing_tag(billing_tag=test_billing_tag)
    assert query_p["totalMatches"] == 1
    assert query_p["page"][0]["id"] == bt_project["id"]
    assert query_p["page"][0]["billingTag"]["tag"] == test_billing_tag

    projects_tags = {bt_project["id"]: test_billing_tag3, project["id"]: test_billing_tag3}
    default_domino_client.project_billing_tag_bulk_update(projects_tags)

    query_p = default_domino_client.projects_by_billing_tag(billing_tag=test_billing_tag3)
    assert query_p["totalMatches"] == 2
    assert query_p["page"][0]["id"] in {bt_project["id"], project["id"]}
    assert query_p["page"][0]["billingTag"]["tag"] == test_billing_tag3
