#!/bin/bash

export build_doc_date=$(date -u '+%d.%m.%Y')

./generate_latex_metadata.sh
./generate_markdown_from_latex.sh

mkdocs serve
