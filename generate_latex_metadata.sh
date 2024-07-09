#!/bin/bash
TEX_DIR='docs/files/tex'
TEX_FILE=${TEX_DIR}
timestamp=$(git log -1 --format=%cd --date=format-local:%d.%m.%Y ${TEX_FILE})
echo "$timestamp" > ${TEX_DIR}/changed.tex

COMMIT=$(git log -1 --pretty=format:"%H" ${TEX_FILE})
echo "\href{https://github.com/tna76874/notentransparenz/tree/${COMMIT}}{Version ${COMMIT}}" > ${TEX_DIR}/commit_github.tex
echo "${COMMIT}" > ${TEX_DIR}/commit.tex