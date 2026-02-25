#!/usr/bin/env bash
# Development quality check script
# Usage:
#   ./scripts/check.sh        - check formatting (exit 1 if changes needed)
#   ./scripts/check.sh --fix  - apply formatting in place

set -euo pipefail

FIX=false
for arg in "$@"; do
  case "$arg" in
    --fix) FIX=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

if $FIX; then
  echo "Running black (format)..."
  uv run black backend/
  echo "Done."
else
  echo "Running black (check)..."
  uv run black --check backend/
  echo "All checks passed."
fi
