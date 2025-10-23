# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = "domino"
author = "Domino Data Lab Inc."
copyright = "2025, Domino Data Lab Inc."
release = "1.4.8"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': False, # Don't show undocumented members
    'show-inheritance': False,
}

# If you want Sphinx to evaluate forward refs safely
set_type_checking_flag = True

# Auto summary settings
autosummary_imported_members = True
autosummary_generate = True

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True

# Autodoc settings
autoclass_content = "both"
autodoc_member_order = "groupwise"

# Mock heavy/optional dependencies to keep autodoc imports lightweight in CI
autodoc_mock_imports = [
    "domino._impl",
    "attrs", "yaml", "pytest",
    "apache_airflow", "airflow",
    "pandas", "numpy", "semver",
    "mlflow", "mlflow_tracing", "mlflow-skinny",
    "requests", "urllib3", "beautifulsoup4", "bs4",
    "polling2", "typing_extensions", "frozendict", "python_dateutil", "dateutil",
    "retry", "docker",
]

# -- Options for HTML output -------------------------------------------------
html_static_path = ['_static']
