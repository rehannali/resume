#!/usr/bin/env bash
set -euo pipefail

# Default actions
IMAGE_NAME="ra/latex"
BUILD=false
CLEAN=false
BUILD_ENV=development
TEXFILE=""

usage() {
  echo "Usage: $0 [OPTIONS] <document.tex>"
  echo
  echo "Options:"
  echo "  --build    Build the Docker image (if not built already or if changes are made)"
  echo "  --clean    Remove the Docker image after running"
  echo "  --release  Use production mode (installs full LaTeX suite)"
  echo "  --help     Show this help message"
  echo
  echo "Examples:"
  echo "  $0 document.tex             # Quick development compile"
  echo "  $0 --release --build thesis.tex # Production build with image rebuild"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)    BUILD=true; shift ;;
        --clean)    CLEAN=true; shift ;;
        --release)  BUILD_ENV="production"; shift ;;
        --help)     usage; exit 0 ;;
        -*)         echo "Unknown option: $1"; usage; exit 1 ;;
        *)          TEXFILE="$1"; shift ;;
    esac
done

[ -z "$TEXFILE" ] && { echo "Error: No input file specified"; usage; exit 1; }

if [ "${BUILD:-false}" = true ]; then
  echo "==== Building Docker image ($BUILD_ENV mode)..."
    docker build -t "$IMAGE_NAME" --build-arg BUILD_ENV="$BUILD_ENV" .
fi

# Run compilation
echo "==== Compiling $TEXFILE in $BUILD_ENV mode..."
docker run --rm \
    -v "$PWD":/data \
    "$IMAGE_NAME" \
    "$TEXFILE"

# Output results
echo "✅ Generated files:"
ls -lh "${TEXFILE%.tex}".{pdf,png} 2>/dev/null || true

# Cleanup if requested
if [ "${CLEAN:-false}" = true ]; then
    echo "==== Removing image..."
    docker rmi "$IMAGE_NAME" || true
fi
