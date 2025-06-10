#!/usr/bin/env bash
# Git pre-push hook to run lint and tests.
set -euo pipefail

# Run ruff if available, otherwise fall back to flake8
if command -v ruff >/dev/null 2>&1; then
    echo "Running ruff..."
    ruff .
elif command -v flake8 >/dev/null 2>&1; then
    echo "Running flake8..."
    flake8 .
else
    echo "Error: neither ruff nor flake8 is installed." >&2
    exit 1
fi

# Run tests
echo "Running pytest..."
PYTEST_QT_STUBS=${PYTEST_QT_STUBS:-0} pytest
