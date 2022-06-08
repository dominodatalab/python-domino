#!/usr/bin/env bash
# testing that job failure works properly w/ the operator
# by throwing an exit code


python -c "import sys; sys.exit(1)"