#!/bin/bash
TEX_DIR='docs/files'
TEX_FILE=${TEX_DIR}/notentransparenz.tex
timestamp=$(git log -1 --format=%cd --date=format-local:%d.%m.%Y ${TEX_FILE})
echo "$timestamp" > ${TEX_DIR}/changed.tex

COMMIT=$(git log -1 --pretty=format:"%H" ${TEX_FILE})
echo "\href{https://github.com/tna76874/notentransparenz/tree/${COMMIT}}{Stand}" > ${TEX_DIR}/commit.tex