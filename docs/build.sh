#!/bin/bash

rm -rf docs/build && pipenv run sphinx-build -M html docs/source docs/build
