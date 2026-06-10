#!/bin/bash
# Fast linting and formatting for Python files under 2 seconds.

if [[ "$1" == *.py ]]; then
    ruff check --fix "$1"
    ruff format "$1"
fi
