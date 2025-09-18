#!/bin/bash

rm -rf docs_build && pipenv run sphinx-build -M html docs/source docs/build
