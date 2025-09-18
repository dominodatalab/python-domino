#!/bin/bash
#
rm -rf docs_build && pipenv run sphinx-build -M html source docs_build
#rm -rf docs_build && pipenv run sphinx-apidoc -f -o docs_build source/generated
