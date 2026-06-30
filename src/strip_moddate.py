import argparse
from pathlib import Path

import pikepdf


def strip_modification_dates(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        
        # 1. Remove xmp:ModifyDate from metadata
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            if 'xmp:ModifyDate' in meta:
                del meta['xmp:ModifyDate']

        # 2. Clear the legacy Info dictionary (handles /ModDate)
        if "/Info" in pdf.trailer:
            del pdf.trailer["/Info"]

        # 3. Save the PDF (preserves original version)
        pdf.save(output_path, fix_metadata_version=False)


def main():
    parser = argparse.ArgumentParser(description='Strip modification dates from a PDF.')
    parser.add_argument('input_pdf', help='Path to the input PDF')

    args = parser.parse_args()

    input_path = Path(args.input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f'Input file "{input_path}" not found.')

    output_path = input_path.parent / f'{input_path.stem}_stripped{input_path.suffix}'

    strip_modification_dates(input_path, output_path)
    print(f'Output saved to "{output_path}"')


if __name__ == '__main__':
    main()
