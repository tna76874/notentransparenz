#!/bin/bash

export build_doc_date=$(date -u '+%d.%m.%Y')
export commit_repo=$(git log -1 --pretty=format:"%H")

./generate_latex_metadata.sh
./generate_markdown_from_latex.sh


mike deploy --update-aliases ${commit_repo} latest
mike set-default latest
mike serve