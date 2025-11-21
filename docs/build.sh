#!/bin/bash

rm -rf docs/build && rm -rf docs/source/generated && pipenv run sphinx-build -M html docs/source docs/build
