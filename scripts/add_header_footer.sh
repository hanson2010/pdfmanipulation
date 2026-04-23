#!/bin/bash

VENV_PYTHON_PATH="/path/to/.venv/bin/python3"
PYTHON_SCRIPT="/path/to/add_header_footer.py"

KAITI_FONT_PATH="/path/to/simkai.ttf"

if [ -z "$KAITI_FONT_PATH" ]; then
    echo "Error: KAITI_FONT_PATH is not set."
    exit 1
fi

export KAITI_FONT_PATH
"$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$@"

PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "Error: Python script failed with exit code $PYTHON_EXIT_CODE."
    exit $PYTHON_EXIT_CODE
fi
