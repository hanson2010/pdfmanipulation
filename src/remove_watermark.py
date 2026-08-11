import argparse
from pathlib import Path

import pikepdf


def _matrix_multiply(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + b1 * c2,
        a1 * b2 + b1 * d2,
        c1 * a2 + d1 * c2,
        c1 * b2 + d1 * d2,
        e1 * a2 + f1 * c2 + e2,
        e1 * b2 + f1 * d2 + f2,
    )


def _covers_page(matrix, page_width, page_height, threshold=0.9):
    a, b, c, d, e, f = matrix
    xs, ys = [], []
    for x, y in ((0, 0), (1, 0), (0, 1), (1, 1)):
        xs.append(a * x + c * y + e)
        ys.append(b * x + d * y + f)
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    return width >= page_width * threshold and height >= page_height * threshold


def _is_rotated(matrix, tolerance=0.0872):
    """True if the CTM has a rotation/shear component beyond ~5 degrees
    (tolerance == sin(5deg); axis-aligned content has b == c == 0). 5 degrees stays
    well clear of incidental skew/rounding noise from PDF generators while still
    catching deliberately-diagonal watermark placement (typically 30-60 degrees)."""
    a, b, c, d, _e, _f = matrix
    scale_x = (a * a + b * b) ** 0.5
    scale_y = (c * c + d * d) ** 0.5
    if scale_x < 1e-9 or scale_y < 1e-9:
        return False
    return abs(b) / scale_x > tolerance or abs(c) / scale_y > tolerance


def _is_mostly_transparent_image(xobject, threshold=0.2):
    """True if an Image XObject's /SMask (alpha channel) is mostly transparent.
    Real embedded photos/scans are essentially never like this; it's the signature
    of a watermark/stamp that was pre-rendered (including any rotation) into pixels,
    leaving no PDF-level matrix, name, or tag to detect it by otherwise."""
    smask = xobject.get('/SMask')
    if smask is None:
        return False
    try:
        raw = pikepdf.PdfImage(smask).as_pil_image().convert('L').tobytes()
        average = sum(raw) / len(raw)
    except Exception:
        return False
    return (average / 255) < threshold


def _oc_names(oc):
    """Yield every OCG /Name reachable from an /OC entry: a plain OCG, or an OCMD
    (Optional Content Membership Dictionary) wrapping one or more OCGs in /OCGs.
    Reads the dictionary directly rather than cross-referencing the document
    catalog's /OCProperties, which real-world PDFs don't always bother registering
    optional content groups in even when they use them."""
    if oc is None:
        return
    if str(oc.get('/Type', '')) == '/OCMD':
        ocgs = oc.get('/OCGs')
        if ocgs is None:
            return
        candidates = ocgs if isinstance(ocgs, pikepdf.Array) else [ocgs]
        for ocg in candidates:
            yield str(ocg.get('/Name', ''))
    else:
        yield str(oc.get('/Name', ''))


def _is_watermark_oc(oc):
    return any('watermark' in name.lower() for name in _oc_names(oc))


def _resolve_oc(tag, properties):
    if isinstance(tag, pikepdf.Name):
        return properties.get(str(tag))
    return tag if hasattr(tag, 'objgen') else None


def _is_watermark_xobject(name, xobject):
    if 'watermark' in str(name).lower():
        return True
    return _is_watermark_oc(xobject.get('/OC'))


def _clean_page(pdf, page, remove_background):
    if '/Annots' in page:
        page.Annots = pikepdf.Array(
            a for a in page.Annots if str(a.get('/Subtype', '')) != '/Watermark'
        )

    media_box = page.mediabox
    page_width = float(media_box[2]) - float(media_box[0])
    page_height = float(media_box[3]) - float(media_box[1])

    resources = page.get('/Resources', {})
    xobjects = resources.get('/XObject', {})
    properties = resources.get('/Properties', {})

    instructions = pikepdf.parse_content_stream(page)
    kept = []
    matrix_stack = [(1, 0, 0, 1, 0, 0)]
    skip_stack = []

    for instr in instructions:
        operator = str(instr.operator)
        operands = instr.operands
        currently_skipping = any(skip_stack)

        if operator == 'q':
            matrix_stack.append(matrix_stack[-1])
        elif operator == 'Q':
            if len(matrix_stack) > 1:
                matrix_stack.pop()
        elif operator == 'cm':
            cm = tuple(float(v) for v in operands)
            matrix_stack[-1] = _matrix_multiply(cm, matrix_stack[-1])
        elif operator == 'BDC':
            skip_this = False
            if not currently_skipping and len(operands) >= 2 and str(operands[0]) == '/OC':
                oc = _resolve_oc(operands[1], properties)
                if _is_watermark_oc(oc):
                    skip_this = True
            skip_stack.append(skip_this)
            if currently_skipping or skip_this:
                continue
            kept.append(instr)
            continue
        elif operator == 'EMC':
            if skip_stack:
                skip_stack.pop()
            if currently_skipping:
                continue
            kept.append(instr)
            continue

        if currently_skipping:
            continue

        if operator == 'Do':
            xobject = xobjects.get(str(operands[0]))
            if xobject is not None:
                if _is_watermark_xobject(operands[0], xobject):
                    continue
                if _is_rotated(matrix_stack[-1]):
                    continue
                is_image = str(xobject.get('/Subtype', '')) == '/Image'
                if is_image and _is_mostly_transparent_image(xobject):
                    continue
                if remove_background and is_image and _covers_page(matrix_stack[-1], page_width, page_height):
                    continue

        kept.append(instr)

    page.Contents = pdf.make_stream(pikepdf.unparse_content_stream(kept))


def remove_watermark(input_path, output_path, remove_background=False):
    with pikepdf.open(str(input_path)) as pdf:
        for page in pdf.pages:
            _clean_page(pdf, page, remove_background)
        pdf.save(str(output_path))


def main():
    parser = argparse.ArgumentParser(description='Remove watermarks (and optionally backgrounds) from a PDF.')
    parser.add_argument(
        '--remove-background', action='store_true',
        help='Also strip images that cover the full page (treated as a background layer)'
    )

    args, remaining = parser.parse_known_args()
    input_pdf = remaining[0] if remaining else None
    if not input_pdf:
        parser.error('the following arguments are required: input_pdf')

    input_path = Path(input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f'Input file "{input_path}" not found.')

    output_path = input_path.parent / f'{input_path.stem}_dewatermarked{input_path.suffix}'

    remove_watermark(input_path, output_path, args.remove_background)
    print(f'Output saved to "{output_path}"')


if __name__ == '__main__':
    main()
