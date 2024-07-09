#!/bin/bash
export TEX_DIR='docs/files/tex'
export VERSION_DIR="${TEX_DIR}/_version"
export DATE_FORMAT='%d.%m.%Y'

mkdir -p ${VERSION_DIR}

timestamp_tex=$(git log -1 --format=%cd --date=format-local:${DATE_FORMAT} ${TEX_DIR})
timestamp_tex_iso=$(git log -1 --format=%cd --date=format-local:'%Y-%m-%d' ${TEX_DIR})
commit_tex=$(git log -1 --pretty=format:"%H" ${TEX_DIR})
commit_count_tex=$(git log --since="$timestamp_tex_iso 00:00:00" --until="$timestamp_tex_iso 23:59:59" --format=%H -- "${TEX_DIR}" | wc -l)

timestamp_repo=$(git log -1 --format=%cd --date=format-local:${DATE_FORMAT})
commit_repo=$(git log -1 --pretty=format:"%H")

# EXPORTING IN LATEX FILES
echo "$timestamp_tex" > ${VERSION_DIR}/timestamp_tex.tex
echo "$commit_count_tex" > ${VERSION_DIR}/commit_count_tex.tex
echo "$timestamp_repo" > ${VERSION_DIR}/timestamp_repo.tex

echo "\href{https://transparenz.hilberg.eu/${commit_repo}/files/tex/notentransparenz.pdf}{${commit_tex}}" > ${VERSION_DIR}/commit_tex.tex
echo "\href{https://transparenz.hilberg.eu/${commit_repo}}{${commit_repo}}" > ${VERSION_DIR}/commit_repo.tex
