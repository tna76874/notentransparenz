#!/bin/bash

rm ./docs/files/tex/*.bbl
rm ./docs/files/tex/*.aux

cat << EOF > ./docs/files/tex/pipeline.tex
\setboolean{simple}{true}
EOF
