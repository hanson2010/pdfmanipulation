#!/bin/bash

VENV_PYTHON_PATH="/path/to/.venv/bin/python3"
PYTHON_SCRIPT="/path/to/sign_with_pfx.py"

PFX_PATH="/path/to/cert.pfx"
SIG_IMAGE_PATH="/path/to/sig.png"
IOSEVKA_FONT_PATH="/path/to/Iosevka-Light.ttc"

if ! command -v "$VENV_PYTHON_PATH" >/dev/null 2>&1 && [ ! -x "$VENV_PYTHON_PATH" ]; then
    echo "Error: Python interpreter '$VENV_PYTHON_PATH' not found."
    echo "Set VENV_PYTHON_PATH to your venv python (e.g. /path/to/.venv/bin/python3)."
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script '$PYTHON_SCRIPT' not found."
    exit 1
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.pdf> [--password <pass>]"
    echo "       [--page <N>] [--x <X>] [--y <Y>] [--timestamp <\"YYYY-MM-DD HH:MM:SS\">]"
    echo ""
    echo "  input.pdf    : Input PDF file"
    echo "  --password   : PFX password (default: empty)"
    echo "  --page       : Page number to sign, 1-based (default: 1)"
    echo "  --x          : X coordinate in pt from left edge (default: 85), approximately 30mm"
    echo "  --y          : Y coordinate in pt from top edge (default: 425), approximately 150mm"
    echo "  --timestamp  : Timestamp string (default: current date/time)"
    exit 1
fi

INPUT_PDF="$1"
shift

if [ ! -f "$INPUT_PDF" ]; then
    echo "Error: Input file '$INPUT_PDF' not found."
    exit 1
fi

if [[ ! "$INPUT_PDF" =~ \.pdf$ ]]; then
    echo "Warning: Input file does not have a .pdf extension."
fi

export PFX_PATH
export SIG_IMAGE_PATH
export IOSEVKA_FONT_PATH
"$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$INPUT_PDF" "$@"

PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "Error: Python script failed with exit code $PYTHON_EXIT_CODE."
    exit $PYTHON_EXIT_CODE
fi
