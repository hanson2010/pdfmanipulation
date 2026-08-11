import pikepdf
import pytest

import strip_moddate as sm


def _make_pdf_with_moddate(path):
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta['xmp:ModifyDate'] = '2020-01-01T00:00:00Z'
    pdf.trailer.Info = pdf.make_indirect(pikepdf.Dictionary(ModDate='D:20200101000000Z'))
    pdf.save(path)
    pdf.close()


def test_strip_modification_dates_removes_xmp_and_info(tmp_path):
    input_path = tmp_path / 'input.pdf'
    _make_pdf_with_moddate(input_path)

    output_path = tmp_path / 'output.pdf'
    sm.strip_modification_dates(input_path, output_path)

    with pikepdf.open(output_path) as pdf:
        assert '/Info' not in pdf.trailer
        with pdf.open_metadata() as meta:
            assert 'xmp:ModifyDate' not in meta


def test_main_derives_output_filename(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / 'doc.pdf'
    _make_pdf_with_moddate(input_path)
    monkeypatch.setattr('sys.argv', ['strip_moddate.py', str(input_path)])

    sm.main()

    expected_output = input_path.parent / 'doc_stripped.pdf'
    assert expected_output.exists()
    captured = capsys.readouterr()
    assert f'Output saved to "{expected_output}"' in captured.out


def test_main_raises_for_missing_input(tmp_path, monkeypatch):
    missing = tmp_path / 'missing.pdf'
    monkeypatch.setattr('sys.argv', ['strip_moddate.py', str(missing)])

    with pytest.raises(FileNotFoundError):
        sm.main()
