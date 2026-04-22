import argparse
import getpass
import io
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers, fields
from pyhanko import stamp


_SIG_IMAGE_DISPLAY_HEIGHT = 36
_TIMESTAMP_GAP = 5
_FONT_SIZE = 8


def _get_sig_image_display_size(sig_image_path):
    from reportlab.lib.utils import ImageReader
    img = ImageReader(sig_image_path)
    iw, ih = img.getSize()
    scale = _SIG_IMAGE_DISPLAY_HEIGHT / ih
    return iw * scale, _SIG_IMAGE_DISPLAY_HEIGHT


def get_font_name():
    iosevka_font_path = os.environ.get('IOSEVKA_FONT_PATH')
    try:
        pdfmetrics.registerFont(TTFont('Iosevka Extralight', iosevka_font_path))
        font_name = 'Iosevka Extralight'
    except Exception as e:
        print(f'Warning: Could not load font from {iosevka_font_path}.')
        print(f'Error: {e}')
        font_name = 'Helvetica'
    return font_name


def get_overlay_page(page_width, page_height, x, y,
                     sig_image_path, timestamp_str):
    from reportlab.lib.utils import ImageReader

    display_width, display_height = _get_sig_image_display_size(sig_image_path)
    img_y = page_height - y - display_height
    text_y = img_y - _TIMESTAMP_GAP

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    font_name = get_font_name()
    can.setFont(font_name, _FONT_SIZE)

    can.drawImage(
        sig_image_path, x, img_y,
        width=display_width, height=display_height,
        preserveAspectRatio=True, mask='auto'
    )

    can.drawString(x, text_y, timestamp_str)
    can.save()

    packet.seek(0)
    return PdfReader(packet).pages[0]


def add_signature_overlay(input_path, output_path, page_num, x, y,
                          sig_image_path, timestamp_str):
    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    if page_num < 1 or page_num > len(reader.pages):
        raise ValueError(
            f'Page number {page_num} out of range (1-{len(reader.pages)}).'
        )

    page_height = None
    for i, page in enumerate(reader.pages, start=1):
        if i == page_num:
            media_box = page.mediabox
            page_width = float(media_box.width)
            page_height = float(media_box.height)

            overlay = get_overlay_page(
                page_width, page_height, x, y,
                sig_image_path, timestamp_str
            )
            page.merge_page(overlay)

        writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)
    
    return page_height


def _load_pfx_signer(pfx_path, passphrase=None):
    return signers.SimpleSigner.load_pkcs12(
        pfx_file=pfx_path, passphrase=passphrase,
    )


def _is_password_error(exc):
    msg = str(exc).lower()
    return 'password' in msg or 'pkcs12' in msg or 'decrypt' in msg


def _resolve_pfx_signer(pfx_path, pfx_password=None):
    passphrase = pfx_password.encode('utf-8') if pfx_password else None
    try:
        signer = _load_pfx_signer(pfx_path, passphrase)
        if signer is not None:
            return signer
    except Exception as e:
        if pfx_password or not _is_password_error(e):
            raise
    if not pfx_password:
        pfx_password = getpass.getpass(
            'PFX file is password-protected. Enter password: '
        )
        passphrase = pfx_password.encode('utf-8') if pfx_password else None
        try:
            signer = _load_pfx_signer(pfx_path, passphrase)
            if signer is not None:
                return signer
        except Exception:
            pass
    raise ValueError('Failed to load PFX certificate. Incorrect password?')


def sign_pdf_with_pfx(input_path, output_path, pfx_path, pfx_password,
                      page_num, x, y, sig_image_path, timestamp_str):
    overlay_path = str(
        Path(output_path).with_name(
            Path(output_path).stem + '_overlay.pdf'
        )
    )

    page_height = add_signature_overlay(
        input_path, overlay_path, page_num, x, y,
        sig_image_path, timestamp_str
    )

    signer = _resolve_pfx_signer(pfx_path, pfx_password)

    display_width, display_height = _get_sig_image_display_size(sig_image_path)
    img_y = page_height - y - display_height
    text_y = img_y - _TIMESTAMP_GAP
    field_name = 'Signature'
    sig_box = (
        x, text_y,
        x + display_width, page_height - y,
    )

    with open(overlay_path, 'rb') as doc:
        w = IncrementalPdfFileWriter(doc)

        fields.append_signature_field(
            w, sig_field_spec=fields.SigFieldSpec(
                sig_field_name=field_name,
                box=sig_box,
                on_page=page_num - 1,
            )
        )

        pdf_signer = signers.PdfSigner(
            signers.PdfSignatureMetadata(field_name=field_name),
            signer=signer,
            stamp_style=stamp.TextStampStyle(
                stamp_text='',
                border_width=0,
            ),
        )

        with open(output_path, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    os.remove(overlay_path)
    print(f'Signed PDF saved to "{output_path}"')


def main():
    parser = argparse.ArgumentParser(
        description='Sign a PDF with a PFX certificate, signature image, and timestamp.'
    )
    parser.add_argument('input_pdf', help='Input PDF file')
    parser.add_argument('--password', default=None, help='PFX password')
    parser.add_argument('--page', type=int, default=1, help='Page number to sign (1-based, default: 1)')
    parser.add_argument('--x', type=float, default=85, help='X coordinate in pt from left edge (default: 85)')
    parser.add_argument('--y', type=float, default=425, help='Y coordinate in pt from top edge (default: 425)')
    parser.add_argument('--timestamp', default=None,
                        help='Timestamp string to display (default: current date/time)')

    args = parser.parse_args()

    input_path = Path(args.input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f'Input file "{input_path}" not found.')

    pfx_path = os.environ.get('PFX_PATH')
    if not pfx_path:
        raise EnvironmentError('PFX_PATH environment variable is not set.')
    if not Path(pfx_path).exists():
        raise FileNotFoundError(f'PFX file "{pfx_path}" not found.')

    sig_image_path = os.environ.get('SIG_IMAGE_PATH')
    if not sig_image_path:
        raise EnvironmentError('SIG_IMAGE_PATH environment variable is not set.')
    if not Path(sig_image_path).exists():
        raise FileNotFoundError(f'Signature image "{sig_image_path}" not found.')

    timestamp_str = args.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    output_path = input_path.parent / f'{input_path.stem}_signed{input_path.suffix}'

    sign_pdf_with_pfx(
        str(input_path), str(output_path),
        pfx_path, args.password,
        args.page, args.x, args.y,
        sig_image_path, timestamp_str
    )


if __name__ == '__main__':
    logging.getLogger('pyhanko').setLevel(logging.CRITICAL)
    try:
        main()
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
