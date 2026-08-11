# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A collection of standalone PDF manipulation command-line tools. Each tool is independent — there is no
shared library code between them. See `README.md` for the current list of tools and how to run each one;
this file intentionally doesn't enumerate them, since the set of tools grows over time and this file
documents cross-cutting conventions, not individual tools.

**When adding a new tool, document it in `README.md` (usage, flags, config vars). Don't add tool-specific
detail here — only update this file if the change affects the conventions below for every tool.**

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r requirements-dev.txt   # test dependencies (pytest)
```

There is no linter or CI configured in this repo. There is a `pytest` test suite — see Testing (TDD) below.

### Which Python interpreter to use — Claude Code vs. `scripts/*.sh`

These two are separate and must not be conflated:

- **Claude Code** (you), when running/testing Python directly in this repo (not via `scripts/*.sh`), resolves
  the interpreter itself, highest to lowest priority:
  1. `$PYTHON_ENVS_PATH/pdfmanipulation` — use if that directory exists.
  2. `./.venv` — use if that directory exists.
  3. Otherwise, stop and report the error to the user. Do not fall back to system `python3` and do not create
     a venv on your own.
- **`scripts/*.sh`** (what end users invoke) are unrelated to the above — they keep hardcoding
  `VENV_PYTHON_PATH` as a `/path/to/...` placeholder, per the existing convention documented below. Do not
  change that convention or make the wrappers read `$PYTHON_ENVS_PATH`.

## Testing (TDD)

This repo follows test-driven development: for a bug fix or new behavior, write (or update) a failing test
under `tests/` first, then change the `src/*.py` code to make it pass, then refactor with the test green.
Don't skip straight to the implementation.

- Framework: `pytest`, configured via `pytest.ini` (`pythonpath = src`, so tests import modules straight
  from `src/<name>.py`; `testpaths = tests`).
- Layout: one `tests/test_<name>.py` per `src/<name>.py`, mirroring it 1:1. Shared fixtures live in
  `tests/conftest.py`.
- Fixtures build every input a test needs on the fly (a minimal PDF via `pikepdf.new()`, a self-signed
  PKCS#12 cert via the `cryptography` package, a signature image via `Pillow`) so the suite is fully
  self-contained — it never depends on the machine-specific paths that `scripts/*.sh` hardcode. Tests that
  exercise a tool needing an optional font env var explicitly unset it (`monkeypatch.delenv(...)`) to force
  the built-in fallback font rather than requiring a real font file.
- Test both the pure function and `main()` for each tool: the pure function's transformation of the PDF, and
  `main()`'s argument handling/output-filename convention/`FileNotFoundError` on a missing input.
- Commands:
  ```bash
  pytest                                  # whole suite
  pytest tests/test_<name>.py             # one tool's tests
  pytest tests/test_<name>.py::test_case -v   # one test
  ```
- Run tests with whichever interpreter Claude Code resolved above (`$PYTHON_ENVS_PATH/pdfmanipulation` or
  `./.venv`) — install `requirements-dev.txt` into that same environment first.

## Architecture: the src/ + scripts/ pair

Every tool consists of exactly two files:

- `src/<name>.py` — the actual implementation: a pure function doing the PDF work, plus a `main()` that
  parses args with `argparse` and calls it.
- `scripts/<name>.sh` — a thin bash wrapper that hardcodes machine-specific config (venv interpreter path,
  font paths, certificate paths, etc.) as `/path/to/...` placeholders at the top, exports whatever env vars
  the Python script reads via `os.environ`, then execs the python script with `"$@"`.

When adding a new tool, create both files following this split — config/secrets belong in the `.sh` wrapper
(as env vars), not as CLI flags, and not hardcoded in the `.py` file.

**Important:** the `/path/to/...` placeholders in `scripts/*.sh` are checked in as-is; real machine-specific
paths (venv location, cert/font paths) are filled in locally by whoever runs the tool and are not meant to be
committed. Don't replace the placeholders with real paths when editing these files.

## Conventions in src/*.py

- Output filenames are derived from the input, never overwrite in place:
  `input_path.parent / f'{input_path.stem}_<suffix>{input_path.suffix}'`, where `<suffix>` is a short
  past-tense tag describing what the tool did; the final `main()` prints `Output saved to "<path>"`.
- Validate the input file up front with `Path.exists()` and raise `FileNotFoundError(f'Input file "{path}"
  not found.')` before doing any work.
- Required external config (fonts, certs, and similar machine-specific inputs) is read via
  `os.environ.get(...)` and validated with an explicit error (`EnvironmentError`/`FileNotFoundError`) rather
  than failing deep inside a library call.
- CLI parsing: scripts that take only a required input-file argument use plain
  `parser.add_argument('input_pdf', ...)`. Scripts that also accept optional flags use
  `parser.parse_known_args()` and pull the positional path out of the `remaining` list manually — this lets
  the input file be given anywhere on the command line relative to the flags. Follow whichever pattern
  matches whether the new tool has optional flags.
- Single quotes for strings; 4-space indentation; no type hints in this codebase currently.

## Conventions in scripts/*.sh

- Check each required env var/path is set with `if [ -z "$VAR" ]; then echo "Error: ..."; exit 1; fi` before
  `export`ing it.
- Invoke as `"$VENV_PYTHON_PATH" "$PYTHON_SCRIPT" "$@"`, then check `$?` and propagate the exit code with a
  matching `"Error: Python script failed with exit code $PYTHON_EXIT_CODE."` message.
- All wrappers hard-require the venv: if `VENV_PYTHON_PATH` doesn't point to an existing file, print
  `Error: Virtual environment not found at $VENV_PYTHON_PATH` and `exit 1`. Never fall back to system
  `python3`.
