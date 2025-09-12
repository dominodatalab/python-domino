#!/bin/bash

IN_FILE=$1

# to markdown
md_out=$IN_FILE.md
pandoc -F ./docs/delink.hs -f html -t gfm-raw_html -o $md_out $IN_FILE

echo $md_out
