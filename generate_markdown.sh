#!/bin/bash

basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# GENERATE LATEX MARKDOWN
TEX_DIR='docs/files/tex'
TEX_FILE=notentransparenz.tex
REF_FILE=references.bib
METADATA_FILE=metadata.yml

cd ${TEX_DIR}
pandoc -s "${TEX_FILE}" -o "notentransparenz.md" --katex --bibliography="${REF_FILE}" --metadata-file="${METADATA_FILE}" --no-highlight

# GENERATE JUPYTER MARKDOWN
cd ${basedir}
notebooks_dir="./examples/notebooks"
output_dir="./docs"

mkdir -p ${output_dir}

find "$notebooks_dir" -name "*.ipynb" -exec jupyter nbconvert --to markdown --output-dir=${output_dir} {} \;
