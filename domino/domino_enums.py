from enum import Enum


class BudgetLabel(Enum):
    BILLINGTAG = "BillingTag"
    ORGANIZATION = "Organization"
    PROJECT = "Project"


class BillingTagSettingMode(Enum):
    DISABLED = "Disabled"
    OPTIONAL = "Optional"
    REQUIRED = "Required"


class ProjectVisibility(Enum):
    PRIVATE = "Private"
    PUBLIC = "Public"
    SEARCHABLE = "Searchable"
