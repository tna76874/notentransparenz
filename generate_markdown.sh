#!/bin/bash

basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# GENERATE JUPYTER MARKDOWN
cd ${basedir}
notebooks_dir="./examples/notebooks"
output_dir="./docs"

mkdir -p ${output_dir}

find "$notebooks_dir" -name "*.ipynb" -exec jupyter nbconvert --to markdown --output-dir=${output_dir} {} \;
