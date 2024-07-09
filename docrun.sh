#!/bin/bash

export build_doc_date=$(date -u '+%d.%m.%Y')
export REPO_COMMIT=$(git log -1 --pretty=format:"%H")

./generate_latex_metadata.sh
./generate_markdown_from_latex.sh


mike deploy --update-aliases ${REPO_COMMIT} latest
mike set-default latest
mike serve