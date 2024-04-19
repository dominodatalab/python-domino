import os
from pprint import pprint

from domino import Domino
from domino.constants import BudgetLabel, BillingTagSettingMode

# requires DOMINO_TOKEN_FILE environment variables, or api_token parameter
domino = Domino("sysadmin1/AdminProject", host=os.environ["DOMINO_API_HOST"])

# GET     /budgets/defaults
budget_defaults = domino.get_budget_defaults()

# PUT     /budgets/defaults/:budgetLabel
new_budget_default = domino.update_budget_defaults(BudgetLabel.PROJECT, 0.0003)

# GET    /budgets/overrides
budget_overrides = domino.get_budget_overrides()

# POST    /budgets/overrides
budget_label = BudgetLabel.PROJECT
budget_id = domino.project_id
budget_limit: float = 0.002
post_overrides = domino.create_budget_override(budget_label, budget_id, budget_limit)

# PUT     /budgets/overrides/:labelId
budget_label = BudgetLabel.PROJECT
budget_id = domino.project_id
budget_limit: float = 0.004
updated_overrides = domino.update_budget_override(budget_label, budget_id, budget_limit)

# DELETE  /budgets/overrides/:labelId
deleted_override = domino.delete_budget_override(domino.project_id)

# GET     /budgets/global/alertsSettings
alert_settings = domino.get_budget_alerts_settings()

# PUT     /budgets/global/alertsSettings # ***


# GET     /billingtags
active_billing_tags = domino.get_active_billing_tags()

# POST    /billingtags
new_billing_tags = domino.create_billing_tags(["BillingTag03", "BillingTag04", "BillingTag06"])
# GET     /billingtags/:name
billing_tag_bn = domino.get_active_billing_tag_by_name("BillingTag03")

# DELETE  /billingtags/:name
dlbt = domino.archive_billing_tag("BillingTag03")

# GET     /billingtagSettings
billing_tag_setting = domino.get_billing_tag_settings()

# PUT     /billingtagSettings
bt_settings_up = domino.update_billing_tag_settings_mode(BillingTagSettingMode.OPTIONAL)

# GET     /billingtagSettings/mode
billing_tag_setting_mode = domino.get_billing_tag_settings_mode()




