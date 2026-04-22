#!/bin/bash

VENV_PYTHON_PATH="/path/to/.venv/bin/python3"
PYTHON_SCRIPT="/path/to/add_header_footer.py"

KAITI_FONT_PATH="/path/to/simkai.ttf"

if ! command -v "$VENV_PYTHON_PATH" >/dev/null 2>&1 && [ ! -x "$VENV_PYTHON_PATH" ]; then
    echo "Error: Python interpreter '$VENV_PYTHON_PATH' not found."
    echo "Set VENV_PYTHON_PATH to your venv python (e.g. /path/to/.venv/bin/python3)."
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script '$PYTHON_SCRIPT' not found."
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Usage: $0 <input.pdf> [header text]"
    echo "  input.pdf   : Input PDF file"
    echo "  header text : (Optional) Right-aligned header text"
    exit 1
fi

INPUT_PDF="$1"
HEADER_TEXT="${2:-}"

# Check if input file exists
if [ ! -f "$INPUT_PDF" ]; then
    echo "Error: Input file '$INPUT_PDF' not found."
    exit 1
fi

# Validate PDF extension
if [[ ! "$INPUT_PDF" =~ \.pdf$ ]]; then
    echo "Warning: Input file does not have a .pdf extension."
fi

# Run the Python script
export KAITI_FONT_PATH
if [ -n "$HEADER_TEXT" ]; then
    "$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$INPUT_PDF" "$HEADER_TEXT"
else
    "$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$INPUT_PDF"
fi

# Capture the exit status of the Python script
PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "Error: Python script failed with exit code $PYTHON_EXIT_CODE."
    exit $PYTHON_EXIT_CODE
fi
