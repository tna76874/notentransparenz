#!/bin/bash
export TEX_DIR='docs/files/tex'
export VERSION_DIR="${TEX_DIR}/_version"
export DATE_FORMAT='%d.%m.%Y'

export REPO_COMMIT_URL='https://github.com/tna76874/notentransparenz/commit/'

mkdir -p ${VERSION_DIR}

timestamp_tex=$(git log -1 --format=%cd --date=format-local:${DATE_FORMAT} ${TEX_DIR})
timestamp_tex_iso=$(git log -1 --format=%cd --date=format-local:'%Y-%m-%d' ${TEX_DIR})
commit_tex=$(git log -1 --pretty=format:"%H" ${TEX_DIR})
commit_count_tex=$(git log --since="$timestamp_tex_iso 00:00:00" --until="$timestamp_tex_iso 23:59:59" --format=%H -- "${TEX_DIR}" | wc -l)

timestamp_repo=$(git log -1 --format=%cd --date=format-local:${DATE_FORMAT})
timestamp_repo_iso=$(git log -1 --format=%cd --date=format-local:'%Y-%m-%d')
commit_repo=$(git log -1 --pretty=format:"%H")
commit_count_repo=$(git log --since="$timestamp_repo_iso 00:00:00" --until="$timestamp_repo_iso 23:59:59" --format=%H | wc -l)

# EXPORTING IN LATEX FILES
echo "$timestamp_tex" > ${VERSION_DIR}/timestamp_tex.tex
echo "$commit_count_tex" > ${VERSION_DIR}/commit_count_tex.tex
echo "$timestamp_repo" > ${VERSION_DIR}/timestamp_repo.tex

export VERSION_DOC="${timestamp_tex_iso}v${commit_count_tex}-DOC"
export VERSION_REPO="${timestamp_repo_iso}v${commit_count_repo}"

echo "${VERSION_DOC}" > ${VERSION_DIR}/VERSION_DOC.tex
echo "${VERSION_REPO}" > ${VERSION_DIR}/VERSION_REPO.tex

echo "\href{${REPO_COMMIT_URL}${commit_tex}}{${commit_tex}}" > ${VERSION_DIR}/commit_tex.tex
echo "\href{${REPO_COMMIT_URL}${commit_repo}}{${commit_repo}}" > ${VERSION_DIR}/commit_repo.tex

VERSION_REPO_URL="https://transparenz.hilberg.eu/${VERSION_REPO}"
VERSION_DOC_URL="https://transparenz.hilberg.eu/${VERSION_REPO}/files/tex/notentransparenz.pdf"

echo "\href{${VERSION_DOC_URL}}{${VERSION_DOC}}" > ${VERSION_DIR}/VERSION_DOC_href.tex
echo "\href{${VERSION_REPO_URL}}{${VERSION_REPO}}" > ${VERSION_DIR}/VERSION_href.tex

echo "\href{${VERSION_DOC_URL}}{${VERSION_DOC_URL}}" > ${VERSION_DIR}/VERSION_DOC_href_with_url.tex
echo "\href{${VERSION_REPO_URL}}{${VERSION_REPO_URL}}" > ${VERSION_DIR}/VERSION_href_with_url.tex
