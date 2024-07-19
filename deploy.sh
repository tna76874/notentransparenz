#!/bin/bash

while getopts ":b:" opt; do
  case ${opt} in
    b )
      deploy_branch=$OPTARG
      ;;
    \? )
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

deploy() {
  if [ -n "$deploy_branch" ]; then
    ./generate_markdown.sh
    mike deploy --branch ${deploy_branch} --update-aliases --push ${VERSION_REPO} latest || mike deploy --branch ${deploy_branch} --push ${VERSION_REPO} latest
    mike set-default --branch ${deploy_branch} --push latest
  else
    ./generate_latex_metadata.sh
    ./generate_markdown.sh
    # deploy_branch="gh-pages-local"
    # mike deploy --branch ${deploy_branch} --update-aliases ${VERSION_REPO} latest || mike deploy --branch ${deploy_branch} ${VERSION_REPO} latest
    # mike set-default --branch ${deploy_branch} latest
    # mike serve --branch ${deploy_branch}
    mkdocs serve
  fi
}

export build_doc_date=$(date -u '+%d.%m.%Y')
export REPO_COMMIT=$(git log -1 --pretty=format:%H)
export VERSION_REPO=$(<docs/files/tex/_version/VERSION_REPO.tex)

deploy


