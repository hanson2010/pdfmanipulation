import pikepdf
import pytest
from PyPDF2 import PdfReader

import remove_watermark as rw


def _annot_subtypes(pdf_path):
    with pikepdf.open(pdf_path) as pdf:
        annots = pdf.pages[0].get('/Annots', [])
        return [str(a.get('/Subtype', '')) for a in annots]


def _xobject_do_names(pdf_path):
    with pikepdf.open(pdf_path) as pdf:
        instructions = pikepdf.parse_content_stream(pdf.pages[0])
        return [
            str(instr.operands[0])
            for instr in instructions
            if str(instr.operator) == 'Do'
        ]


def test_removes_watermark_annotation(make_pdf_with_watermark_annotation, tmp_path):
    input_path = make_pdf_with_watermark_annotation()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Watermark' not in _annot_subtypes(output_path)
    assert 'Body text' in PdfReader(str(output_path)).pages[0].extract_text()


def test_removes_ocg_watermark(make_pdf_with_ocg_watermark, tmp_path):
    input_path = make_pdf_with_ocg_watermark()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    text = PdfReader(str(output_path)).pages[0].extract_text()
    assert 'WATERMARK' not in text
    assert 'Body text' in text


def test_removes_unregistered_ocmd_watermark(make_pdf_with_unregistered_ocmd_watermark, tmp_path):
    input_path = make_pdf_with_unregistered_ocmd_watermark()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Fm0' not in _xobject_do_names(output_path)
    text = PdfReader(str(output_path)).pages[0].extract_text()
    assert 'WATERMARK' not in text
    assert 'Body text' in text


def test_removes_named_xobject_watermark(make_pdf_with_named_xobject_watermark, tmp_path):
    input_path = make_pdf_with_named_xobject_watermark()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Watermark' not in _xobject_do_names(output_path)
    text = PdfReader(str(output_path)).pages[0].extract_text()
    assert 'WATERMARK' not in text
    assert 'Body text' in text


def test_removes_rotated_untagged_watermark(make_pdf_with_rotated_watermark, tmp_path):
    input_path = make_pdf_with_rotated_watermark()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Fm0' not in _xobject_do_names(output_path)
    text = PdfReader(str(output_path)).pages[0].extract_text()
    assert 'WATERMARK' not in text
    assert 'Body text' in text


def test_slightly_skewed_image_is_kept(make_pdf_with_slightly_skewed_image, tmp_path):
    input_path = make_pdf_with_slightly_skewed_image()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Im0' in _xobject_do_names(output_path)


def test_removes_transparent_watermark_image(make_pdf_with_transparent_watermark_image, tmp_path):
    input_path = make_pdf_with_transparent_watermark_image()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Im0' not in _xobject_do_names(output_path)
    assert 'Body text' in PdfReader(str(output_path)).pages[0].extract_text()


def test_opaque_masked_image_is_kept(make_pdf_with_opaque_masked_image, tmp_path):
    input_path = make_pdf_with_opaque_masked_image()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    assert '/Im0' in _xobject_do_names(output_path)


def test_background_image_kept_by_default(make_pdf_with_background_image, tmp_path):
    input_path = make_pdf_with_background_image()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path)

    do_names = _xobject_do_names(output_path)
    assert '/Bg' in do_names
    assert '/Small' in do_names


def test_background_image_removed_with_flag(make_pdf_with_background_image, tmp_path):
    input_path = make_pdf_with_background_image()
    output_path = tmp_path / 'output.pdf'

    rw.remove_watermark(input_path, output_path, remove_background=True)

    do_names = _xobject_do_names(output_path)
    assert '/Bg' not in do_names
    assert '/Small' in do_names  # doesn't cover the full page, so it's kept
    assert 'Body text' in PdfReader(str(output_path)).pages[0].extract_text()


def test_main_derives_output_filename(make_pdf_with_watermark_annotation, monkeypatch, capsys):
    input_path = make_pdf_with_watermark_annotation(name='doc.pdf')
    monkeypatch.setattr('sys.argv', ['remove_watermark.py', str(input_path)])

    rw.main()

    expected_output = input_path.parent / 'doc_dewatermarked.pdf'
    assert expected_output.exists()
    captured = capsys.readouterr()
    assert f'Output saved to "{expected_output}"' in captured.out


def test_main_accepts_remove_background_flag_and_positional_in_any_order(
    make_pdf_with_background_image, monkeypatch
):
    input_path = make_pdf_with_background_image(name='doc2.pdf')
    monkeypatch.setattr(
        'sys.argv',
        ['remove_watermark.py', '--remove-background', str(input_path)],
    )

    rw.main()

    expected_output = input_path.parent / 'doc2_dewatermarked.pdf'
    assert '/Bg' not in _xobject_do_names(expected_output)


def test_main_raises_for_missing_input(tmp_path, monkeypatch):
    missing = tmp_path / 'missing.pdf'
    monkeypatch.setattr('sys.argv', ['remove_watermark.py', str(missing)])

    with pytest.raises(FileNotFoundError):
        rw.main()
