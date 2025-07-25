#!/usr/bin/env bash
set -euo pipefail

TEXFILE="$1"
BASE="${BASE_NAME:-RehanAliResume}"
PDF="${BASE}.pdf"
PNG="${BASE}.png"

pdflatex -jobname="$BASE" "$TEXFILE"
pdflatex -jobname="$BASE" "$TEXFILE" || true

echo "=> PDF created: $PDF"

if command -v magick &> /dev/null; then
  echo "Converting PDF to PNG(s) using ImageMagick..."
  magick -density 600 -background white -alpha remove -trim "$PDF" "${OUTPUT_NAME}-%d.png"
else
  echo "Converting PDF to PNG(s) using pdftoppm..."
  pdftoppm -png -r 600 "$PDF" "${BASE}"
fi


echo "=> PNG created: $PNG"

rm -f "${BASE}".{aux,log,out,toc,fls} || true
