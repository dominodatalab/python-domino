#!/bin/bash

# we generate the asciidoc by generating a markdown file first because
# pandoc converts html to asciidoc in a way that we can't render in our user facing docs

base_path=docs/build/html/generated
all_doc=$base_path/domino.agents.md

function replace_carriage_returns() {
  sed -i '' "s/¶//g" $1
}

echo creating single file $all_doc
echo "" > $all_doc

ls $base_path | grep -E 'domino\.agents\.[a-z_]+\.html$' | while read -r file; do
  html_file=$base_path/$file
  adoc=$(./docs/html_to_md.sh $html_file)

  echo new $adoc

  cat $adoc >> $all_doc
  echo "" >> $all_doc
  replace_carriage_returns $all_doc

done

echo ""
echo done making $all_doc

echo ""
echo "making ascii doc"
ASCII_DOC=$(./docs/md_to_adoc.sh $all_doc)
replace_carriage_returns $ASCII_DOC

echo done making asciidoc $ASCII_DOC
