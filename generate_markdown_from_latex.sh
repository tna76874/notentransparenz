#!/bin/bash
TEX_DIR='docs/files'
TEX_FILE=${TEX_DIR}/notentransparenz.tex
REF_FILE=${TEX_DIR}/references.bib
METADATA_FILE=${TEX_DIR}/metadata.yml 

pandoc -s "${TEX_FILE}" -o "${TEX_DIR}/notentransparenz.md" --katex --bibliography="${REF_FILE}" --metadata-file="${METADATA_FILE}"