import argparse
from pathlib import Path

import pikepdf


def remove_password(input_path, output_path):
    pdf = pikepdf.open(str(input_path))
    pdf.save(str(output_path), encryption=False)
    pdf.close()


def main():
    parser = argparse.ArgumentParser(description='Remove password protection from a PDF.')
    parser.add_argument('input_pdf', help='Path to the password-protected PDF')

    args = parser.parse_args()

    input_path = Path(args.input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f'Input file "{input_path}" not found.')

    output_path = input_path.parent / f'{input_path.stem}_decrypted{input_path.suffix}'

    remove_password(input_path, output_path)
    print(f'Output saved to "{output_path}"')


if __name__ == '__main__':
    main()
