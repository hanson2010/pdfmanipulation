#!/bin/bash

VENV_PYTHON_PATH="/path/to/.venv/bin/python3"
PYTHON_SCRIPT="/path/to/convert_spreadsheet_to_csv.py"

if [ ! -f "$VENV_PYTHON_PATH" ]; then
    echo "Warning: Virtual environment not found at $VENV_PYTHON_PATH"
    echo "Falling back to system python3"
    VENV_PYTHON_PATH="python3"
fi

"$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$@"

PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "Error: Python script failed with exit code $PYTHON_EXIT_CODE."
    exit $PYTHON_EXIT_CODE
fi
