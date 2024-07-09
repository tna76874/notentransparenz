#!/bin/bash
TEX_DIR='docs/files/tex'
TEX_FILE=notentransparenz.tex
REF_FILE=references.bib
METADATA_FILE=metadata.yml

cd ${TEX_DIR}
pandoc -s "${TEX_FILE}" -o "notentransparenz.md" --katex --bibliography="${REF_FILE}" --metadata-file="${METADATA_FILE}"