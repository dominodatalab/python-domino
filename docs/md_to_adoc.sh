#!/bin/bash

IN_FILE=$1

# to asciidoc
adoc_out=$IN_FILE.adoc
pandoc -f markdown -t asciidoc -o $adoc_out $IN_FILE

echo $adoc_out
