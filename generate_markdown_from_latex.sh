#!/bin/bash
TEX_DIR='docs/files'
TEX_FILE=${TEX_DIR}/notentransparenz.tex

pandoc -s "${TEX_FILE}" -o "${TEX_DIR}/notentransparenz.md" --mathjax