#!/usr/bin/env python3
"""
Check that no camelCase parameter names are introduced in domino/ source.
Usage: python scripts/check_snake_case.py [file ...]

This is the canonical source of inclusion/exclusion rules — both pre-commit
and CI invoke this script and let it decide which paths to inspect. Paths
outside `domino/` or under the excluded subtrees are silently skipped, so
callers can safely pass globs (e.g. `domino/**/*.py`) or the output of
`find domino -name "*.py"` without pre-filtering.
"""

import ast
import re
import sys

CAMEL_RE = re.compile(r"^[a-z][a-z0-9]*[A-Z]")
IGNORE = {"setUp", "tearDown", "setUpClass", "tearDownClass"}

# Anchored regex equivalents of pre-commit's `files:` / `exclude:` config.
INCLUDE_RE = re.compile(r"^domino/.*\.py$")
EXCLUDE_RE = re.compile(r"^domino/_impl/|^domino/airflow/")


def should_check(path: str) -> bool:
    return bool(INCLUDE_RE.match(path)) and not EXCLUDE_RE.match(path)


def check_file(path: str) -> list[tuple[int, str]]:
    violations = []
    with open(path) as f:
        tree = ast.parse(f.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args + node.args.kwonlyargs:
                if CAMEL_RE.match(arg.arg) and arg.arg not in IGNORE:
                    violations.append((node.lineno, arg.arg))
    return violations


if __name__ == "__main__":
    files = sys.argv[1:] or []
    found = False
    for path in files:
        if not should_check(path):
            continue
        for lineno, name in check_file(path):
            print(f"{path}:{lineno}: camelCase parameter '{name}'")
            found = True
    sys.exit(1 if found else 0)
