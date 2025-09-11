# Configuration file for the Sphinx documentation builder.

import os
import sys

# Make the project importable by Sphinx (repo root on sys.path)
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
project = "domino"
author = "Domino Data Lab Inc."
copyright = "2025, Domino Data Lab Inc."
release = "0.0.1"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx_multiversion",
]

# If you want Sphinx to evaluate forward refs safely
set_type_checking_flag = True

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autoclass_content = "both"
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Mock heavy/optional dependencies to keep autodoc imports lightweight in CI
autodoc_mock_imports = [
    "apache_airflow", "airflow",
    "pandas", "numpy", "semver",
    "mlflow", "mlflow_tracing", "mlflow-skinny",
    "requests", "urllib3", "beautifulsoup4", "bs4",
    "polling2", "typing_extensions", "frozendict", "python_dateutil", "dateutil",
    "retry", "docker",
]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

# sphinx-multiversion configuration: build main/master and version tags
smv_branch_whitelist = r"^(main|master)$"
smv_tag_whitelist = r"^(v\d+\.\d+\.\d+|(R|r)elease-.*)$"
smv_remote_whitelist = r"^origin$"
