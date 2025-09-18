#!/bin/bash

base_path=docs/build/html/generated
all_doc=$base_path/domino.aisystems.adoc

echo creating single file $all_doc
echo "" > $all_doc

ls $base_path | grep -E 'domino\.aisystems\.[a-z_]+\.html$' | while read -r file; do
  html_file=$base_path/$file
  adoc=$html_file.adoc
  pandoc -f html -t asciidoc -o $adoc $html_file

  echo new $adoc

  cat $adoc >> $all_doc
  echo "" >> $all_doc

done

echo ""
echo done making $all_doc

