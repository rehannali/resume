#!/usr/bin/env bash
set -euo pipefail

# Default actions
do_build=false
do_clean=false

usage() {
  echo "Usage: $0 [--build] [--clean] <document.tex>"
  echo "  --build    Build the Docker image (if not built already)"
  echo "  --clean    Remove the Docker image after running"
  exit 1
}

# Parse long options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)   do_build=true; shift ;;
    --clean)   do_clean=true; shift ;;
    --help)    usage ;;
    -*)
      echo "Unknown flag: $1"
      usage ;;
    *) break ;;
  esac
done

if [ $# -lt 1 ]; then
  usage
fi

TEXFILE="$1"

if $do_build; then
  echo "==== Building Docker image 'ra/latex'..."
  docker build -t ra/latex .
fi

echo "==== Running container to compile '$TEXFILE'..."
docker run --rm -v "$PWD":/data ra/latex "$TEXFILE"

echo "✅ Files generated: ${TEXFILE%.tex}.pdf, ${TEXFILE%.tex}.png"

if $do_clean; then
  echo "==== Cleaning up image 'ra/latex'..."
  docker rmi ra/latex || true
fi
