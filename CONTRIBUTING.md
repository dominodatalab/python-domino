# Contributing

## Running checks locally

The CI pipeline runs four categories of checks. You can run all of them locally before pushing.

### Formatting (auto-fixable)

`black` and `isort` can reformat your code in place:

```bash
pip install black==25.1.0 isort==5.13.2

# auto-fix
black .
isort .

# check only (what CI does)
black --check .
isort --check .
```

### Linting

```bash
pip install "flake8==7.2.0"
flake8 .
```

flake8 does not auto-fix. Check `.flake8` for project-specific rules (ignored codes, max line length, complexity threshold).

### Type checking

```bash
pip install -e .
pip install "mypy==1.15.0" \
  types-pyyaml types-requests types-retry types-pytz \
  types-tabulate types-python-dateutil types-redis \
  types-protobuf types-frozendict types-urllib3

mypy domino/ \
  --no-warn-no-return \
  --namespace-packages \
  --explicit-package-bases \
  --ignore-missing-imports \
  --follow-imports=silent \
  --python-version=3.10
```

### Snake case (new parameters only)

A lightweight AST check ensures new parameters in `domino/` use `snake_case`:

```bash
python scripts/check_snake_case.py domino/domino.py
```

This check is scoped to `domino/` source files only and ignores existing camelCase parameters that are kept for backwards compatibility.

### Tests

```bash
pip install pytest pytest-cov requests-mock docker pytest-mock
pytest tests/ \
  --ignore=tests/agents \
  --ignore=tests/integration \
  --ignore=tests/scripts \
  --ignore=tests/test_operator.py \
  --ignore=tests/test_spark_operator.py \
  -v --tb=short
```

The ignored paths either require a live Domino deployment (`tests/integration`) or optional dependencies not installed by default (`tests/agents`, `tests/test_operator.py`, and `tests/test_spark_operator.py` require `apache-airflow` or the tracing extras).

### Pre-commit (optional)

You can run all checks automatically on every commit by installing the pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

To run them manually against all files:

```bash
pre-commit run --all-files
```
