import os
from pprint import pprint
import uuid

from domino import Domino
from domino.domino_enums import BudgetLabel, BillingTagSettingMode


def get_uuid() -> str:
    return str(uuid.uuid4())[:8]


# requires DOMINO_TOKEN_FILE environment variables, or api_token parameter
domino = Domino("sysadmin1/AdminProject", host=os.environ["DOMINO_API_HOST"])

# budgets defaults get and update
# get budget defaults
budget_defaults = domino.budget_defaults_list()
pprint(budget_defaults)

# update budget defaults
new_limit = 0.10101
domino.budget_defaults_update(BudgetLabel.PROJECT, new_limit)
newer_defaults = domino.budget_defaults_list()
pprint(newer_defaults)

# budgets overrides crud
# get budget overrides
budget_overrides = domino.budget_overrides_list()
pprint(budget_overrides)

# create budget overrides
budget_label = BudgetLabel.PROJECT
budget_id = domino.project_id
budget_limit: float = 0.002
new_overrides = domino.budget_override_create(budget_label, budget_id, budget_limit)
pprint(new_overrides)

# update budget overrides
new_limit: float = 0.004
updated_overrides = domino.budget_override_update(budget_label, budget_id, new_limit)
pprint(updated_overrides)

budget_overrides = domino.budget_overrides_list()
pprint(budget_overrides)

# delete budget overrides
deleted_override = domino.budget_override_delete(domino.project_id)
pprint(deleted_override)

budget_overrides = domino.budget_overrides_list()
pprint(budget_overrides)

# budgets alertsSettings get and update
# get budgets alertsSettings
alert_settings = domino.budget_alerts_settings()
pprint(alert_settings)

# update budgets alertsSettings (enablement and notifications)
domino.budget_alerts_settings_update(alerts_enabled=False, notify_org_owner=False)
updated_setting = domino.budget_alerts_settings()
pprint(updated_setting)

domino.budget_alerts_settings_update(alerts_enabled=True, notify_org_owner=True)
updated_setting_2 = domino.budget_alerts_settings()
pprint(updated_setting_2)

# update budgets alertsSettings email targets
# IMPORTANT: billingTag targets are required to set budgets by billing tags
new_email_targets = {
    BudgetLabel.PROJECT.value: ["projectszzz@gmail.com"],
    BudgetLabel.BILLINGTAG.value: ["orgzyyy@gmail.com", "billingTAgs@gmail.com"],
}

domino.budget_alerts_targets_update(new_email_targets)
updated_setting_targets = domino.budget_alerts_settings()
pprint(updated_setting_targets)

# billingtag settings get and update
# get billingtag settings
bt_setting = domino.billing_tag_settings()
pprint(bt_setting)

# update billingtag settings modes
bt_settings_optional = domino.billing_tag_settings_mode_update(BillingTagSettingMode.OPTIONAL)
bt_setting = domino.billing_tag_settings()
pprint(bt_setting)

# get billingtag settings mode
bt_setting_mode = domino.billing_tag_settings_mode()
pprint(bt_setting_mode)

# billingtags crud
# get list of active billingtags
active_billing_tags = domino.active_billing_tags_list()
pprint(active_billing_tags)

# create new or unarchive existing billingtags
new_billing_tags = domino.billing_tags_create(["BTExample003", "BTExample04", "BTExample06"])
active_billing_tags = domino.active_billing_tags_list()
pprint(active_billing_tags)

# get billingtags info by name
billing_tag_bn = domino.active_billing_tag_by_name("BTExample003")
pprint(billing_tag_bn)

# archive billingtags
deleted_bt = domino.billing_tag_archive("BTExample003")
pprint(deleted_bt)

# projects and billing tags
# get projects by billing tags
projects_by_bt = domino.projects_by_billing_tag(billing_tag="BTExample003")
pprint(projects_by_bt)

# create projects with billing tags (billing tags settings mode must be Optional or Required)
example_project_name = f"example-project-{get_uuid()}"
bt_project = domino.project_create_v4(project_name=example_project_name, billing_tag="BTExample04")
pprint(bt_project)

# create projects with billing tags (billing tags settings mode must be Optional or Disabled)
example_project_name_2 = f"example-project-{str(uuid.uuid4())}"
project = domino.project_create_v4(project_name=example_project_name_2)
pprint(project)

# get billing tag of particular project
project_bt = domino.project_billing_tag(bt_project["id"])
pprint(project_bt)

# update a project's billing tags
domino.project_billing_tag_update("BTExample06", project["id"])
project_update = domino.project_billing_tag(project["id"])
pprint(project_update)

# remove a billing tag from a project
domino.project_billing_tag_reset(project["id"])
project_bt_reset = domino.project_billing_tag(project["id"])
pprint(project_bt_reset)

# query project by billing tag (see code for other possible fields)
projects_bt_04 = domino.projects_by_billing_tag(billing_tag="BTExample04")
pprint(projects_bt_04)

# update projects' billing tags in bulk
projects_tags = {bt_project["id"]: "BTExample06", project["id"]:  "BTExample06", domino.project_id: "BTExample04"}
domino.project_billing_tag_bulk_update(projects_tags)

# query project by billing tag
projects_bt_06 = domino.projects_by_billing_tag(billing_tag="BTExample06")
pprint(projects_bt_06)

# query project by billing tag
projects_bt_04 = domino.projects_by_billing_tag(billing_tag="BTExample04")
pprint(projects_bt_04)