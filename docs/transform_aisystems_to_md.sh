#!/bin/bash

base_path=docs/build/html/generated
all_doc=$base_path/domino.aisystems.md

echo creating single file $all_doc
echo "" > $all_doc

ls $base_path | grep -E 'domino\.aisystems\.[a-z_]+\.html$' | while read -r file; do
  html_file=$base_path/$file
  adoc=$html_file.md
  pandoc -f html -t gfm-raw_html -o $adoc $html_file

  echo new $adoc

  cat $adoc >> $all_doc
  echo "" >> $all_doc

done

echo ""
echo done making $all_doc

echo ""
echo "making ascii doc"
ASCII_DOC=$all_doc.adoc

pandoc -f markdown -t asciidoc -o $ASCII_DOC $all_doc

echo done making asciidoc $ASCII_DOC
