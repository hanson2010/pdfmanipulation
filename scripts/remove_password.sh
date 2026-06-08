#!/bin/bash

VENV_PYTHON_PATH="/path/to/.venv/bin/python3"
PYTHON_SCRIPT="/path/to/remove_password.py"

if [ -z "$1" ]; then
    echo "Usage: $0 <input_pdf>"
    exit 1
fi

"$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$1"

PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "Error: Python script failed with exit code $PYTHON_EXIT_CODE."
    exit $PYTHON_EXIT_CODE
fi
