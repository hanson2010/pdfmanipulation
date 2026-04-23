#!/bin/bash

VENV_PYTHON_PATH="/path/to/.venv/bin/python3"
PYTHON_SCRIPT="/path/to/sign_with_pfx.py"

PFX_PATH="/path/to/cert.pfx"
SIG_IMAGE_PATH="/path/to/sig.png"
IOSEVKA_FONT_PATH="/path/to/Iosevka-Light.ttc"

if [ -z "$PFX_PATH" ]; then
    echo "Error: PFX_PATH is not set."
    exit 1
fi

if [ -z "$SIG_IMAGE_PATH" ]; then
    echo "Error: SIG_IMAGE_PATH is not set."
    exit 1
fi

if [ -z "$IOSEVKA_FONT_PATH" ]; then
    echo "Error: IOSEVKA_FONT_PATH is not set."
    exit 1
fi

export PFX_PATH
export SIG_IMAGE_PATH
export IOSEVKA_FONT_PATH
"$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$@"

PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "Error: Python script failed with exit code $PYTHON_EXIT_CODE."
    exit $PYTHON_EXIT_CODE
fi
