import pytest
import uuid

from domino.domino_enums import BillingTagSettingMode, BudgetLabel
from domino.helpers import domino_is_reachable


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


@pytest.mark.skipif(  #
    not domino_is_reachable(), reason="No access to a live Domino deployment"
)
def test_budgets_alerts_settings(default_domino_client):  # TODO
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
