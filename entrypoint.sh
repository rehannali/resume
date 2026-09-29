#!/usr/bin/env bash
set -euo pipefail

TEXFILE="$1"
BASE="${BASE_NAME:-RehanAli_Resume}"
FULL="${BASE}_Full"
BRIEF="${BASE}_Brief"

# Remove all PDF and PNG files if any exist
shopt -s nullglob  # So globs return empty instead of literal pattern if no match

files=( *.pdf *.png )
if [ ${#files[@]} -gt 0 ]; then
  echo "🧹 Removing existing PDF/PNG files..."
  rm -f "${files[@]}"
else
  echo "ℹ️ No PDF or PNG files to remove."
fi

build_variant() {
  local jobname="$1"
  local texinput="$2"
  local pdf="${jobname}.pdf"

  echo "==== Building variant: $jobname"
  pdflatex -jobname="$jobname" "$texinput"
  pdflatex -jobname="$jobname" "$texinput" || true

  echo "=> PDF created: $pdf"

  if command -v magick &> /dev/null; then
    echo "Converting PDF to PNG(s) using ImageMagick..."
    magick -density 600 "$pdf" -background white -alpha remove "${jobname}-%d.png"
  else
    echo "Converting PDF to PNG(s) using pdftoppm..."
    pdftoppm -png -r 600 "$pdf" "${jobname}"
  fi

  count=$(ls "${jobname}"*.png 2>/dev/null | wc -l)
  echo "=> $count PNG file(s) created:"
  ls -1 "${jobname}"*.png 2>/dev/null || echo "No PNGs found"

  rm -f "${jobname}".{aux,log,out,toc,fls} || true
}

# Full resume (with PROJECTS section)
build_variant "$FULL" "$TEXFILE"

# Brief resume (without the PROJECTS section)
build_variant "$BRIEF" "\\def\\NOPROJECTS{1}\\input{$TEXFILE}"
