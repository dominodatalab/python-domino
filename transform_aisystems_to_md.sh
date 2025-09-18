#!/bin/bash
#
base_path=docs_build/html/generated
all_doc=$base_path/domino.aisystems.md

echo creating single file $all_doc
echo "" > $all_doc

ls $base_path | grep -E 'domino\.aisystems\.[a-z_]+\.html$' | while read -r file; do
  html_file=$base_path/$file
  md=$html_file.md.txt
  pandoc -f html -t markdown -o $md $html_file

  adoc=$html_file.md
  # to github markdown
  pandoc -f markdown -t gfm -o $adoc $md


  echo new $adoc

  cat $adoc >> $all_doc
  echo "" >> $all_doc

done

echo ""
echo done making $all_doc

