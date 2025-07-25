#!/usr/bin/env bash
set -euo pipefail

TEXFILE="$1"
BASE="RehanCV"
PDF="${BASE}.pdf"
PNG="${BASE}.png"

pdflatex -jobname="$BASE" "$TEXFILE"
pdflatex -jobname="$BASE" "$TEXFILE" || true

echo "=> PDF created: $PDF"

if command -v magick &> /dev/null; then
  magick -density 300 -background white -alpha remove -trim "$PDF" "$PNG"
else
  pdftoppm -png -r 300 "$PDF" "${BASE}"
  mv "${BASE}-1.png" "$PNG"
fi

echo "=> PNG created: $PNG"

rm -f "${BASE}".{aux,log,out,toc,fls} || true
