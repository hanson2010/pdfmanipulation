#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse


def convert_spreadsheet_to_csv(input_path: Path, output_dir: Path = None, sheet: str = None):
    file_ext = input_path.suffix.lower()
    if file_ext not in (".xls", ".xlsx", ".ods"):
        raise RuntimeError(f"Unsupported spreadsheet type {file_ext}")

    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError(
            "pandas not installed. Please install it first with "
            "'pip install pandas openpyxl odfpy'."
        )

    if output_dir is None:
        output_dir = input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = input_path.stem

    if sheet is not None:
        sheets = [sheet]
    else:
        try:
            sheets = pd.ExcelFile(str(input_path)).sheet_names
        except Exception:
            sheets = [0]

    written = []
    for idx, sheet_name in enumerate(sheets):
        df = pd.read_excel(str(input_path), sheet_name=sheet_name, engine=None)
        if sheet is not None:
            output_file = output_dir / f"{base_name}.csv"
        elif len(sheets) == 1:
            output_file = output_dir / f"{base_name}.csv"
        else:
            safe_name = str(sheet_name).replace("/", "-")
            output_file = output_dir / f"{base_name}_{idx + 1:02d}_{safe_name}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8")
        written.append(output_file)

    return written


def main():
    parser = argparse.ArgumentParser(
        description="Convert xls/xlsx/ods spreadsheets to CSV."
    )
    parser.add_argument(
        "input_pattern",
        help="Input file or wildcard pattern (quote patterns like '*.xlsx')",
    )
    parser.add_argument(
        "-o", "--output-dir", help="Output directory (default: same as input file directory)"
    )
    parser.add_argument(
        "-s", "--sheet", help="Name of a single sheet to convert (default: all sheets)"
    )

    args = parser.parse_args()

    pattern_path = Path(args.input_pattern)

    if pattern_path.is_absolute():
        input_paths = list(pattern_path.parent.glob(pattern_path.name))
    else:
        input_paths = list(Path.cwd().glob(args.input_pattern))

    output_dir = Path(args.output_dir) if args.output_dir else None

    if input_paths:
        print(f"Found {len(input_paths)} file(s) matching '{args.input_pattern}':")
        for p in input_paths:
            print(f"  - {p}")
        for input_path in input_paths:
            if input_path.is_file():
                try:
                    written = convert_spreadsheet_to_csv(input_path, output_dir, args.sheet)
                    for f in written:
                        print(f"Written to {f}")
                except Exception as e:
                    print(f"Error processing {input_path}: {e}", file=sys.stderr)
            else:
                print(f"Skipping {input_path}: not a file", file=sys.stderr)
    else:
        print(f"No files found matching {args.input_pattern}", file=sys.stderr)


if __name__ == "__main__":
    main()
