#!/usr/bin/env bash
set -euo pipefail

TEXFILE="$1"
BASE="${BASE_NAME:-RehanAliResume}"
PDF="${BASE}.pdf"
PNG="${BASE}.png"

# Remove all PDF and PNG files if any exist
shopt -s nullglob  # So globs return empty instead of literal pattern if no match

files=( *.pdf *.png )
if [ ${#files[@]} -gt 0 ]; then
  echo "🧹 Removing existing PDF/PNG files..."
  rm -f "${files[@]}"
else
  echo "ℹ️ No PDF or PNG files to remove."
fi

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


count=$(ls ${BASE}*.png 2>/dev/null | wc -l)
echo "=> $count PNG file(s) created:"
ls -1 ${BASE}*.png 2>/dev/null || echo "No PNGs found"

rm -f "${BASE}".{aux,log,out,toc,fls} || true
