import argparse
import io, os
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


MARGIN = 40
FOOTER_Y = 30


def get_page_size(page):
    media_box = page.mediabox
    width = float(media_box.width)
    height = float(media_box.height)
    return width, height


def get_font_name():
    kaiti_font_path = os.environ.get('KAITI_FONT_PATH')
    try:
        pdfmetrics.registerFont(TTFont('KaiTi', kaiti_font_path))
        font_name = 'KaiTi'
    except Exception as e:
        print(f'Warning: Could not load font from {kaiti_font_path}.')
        print(f'Error: {e}')
        font_name = 'Helvetica'
    return font_name


def add_header_footer(input_path, output_path, header_text=None):
    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages, start=1):
        PAGE_WIDTH, PAGE_HEIGHT = get_page_size(page)
        HEADER_Y = PAGE_HEIGHT - MARGIN
        RIGHT_X = PAGE_WIDTH - MARGIN

        # Create a new PDF with header/footer text
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=get_page_size(page))
        can.setFont(get_font_name(), 12)

        # Add header if provided (right-aligned at top)
        if header_text:
            can.drawRightString(RIGHT_X, HEADER_Y, header_text)

        # Add footer (centered at bottom)
        footer_text = f'–{i}–'
        can.drawCentredString(PAGE_WIDTH / 2, FOOTER_Y, footer_text)

        can.save()

        # Merge the overlay (header/footer) with the original page
        packet.seek(0)
        overlay = PdfReader(packet).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    # Write the final PDF
    with open(output_path, 'wb') as f:
        writer.write(f)


def main():
    parser = argparse.ArgumentParser(description='Add header and footer to a PDF.')
    parser.add_argument('input_pdf', help='Input PDF file')
    parser.add_argument(
        'header_text', nargs='?', default=None, help='Header text (right-aligned, optional)'
    )

    args = parser.parse_args()

    input_path = Path(args.input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f'Input file "{input_path}" not found.')

    # Generate output filename
    output_path = input_path.parent / f'{input_path.stem}_stamped{input_path.suffix}'

    add_header_footer(input_path, output_path, args.header_text)
    print(f'Output saved to "{output_path}"')


if __name__ == '__main__':
    main()
