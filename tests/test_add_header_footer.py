from PyPDF2 import PdfReader
import pytest

import add_header_footer as ahf


@pytest.fixture(autouse=True)
def _no_kaiti_font(monkeypatch):
    # Force the Helvetica fallback so tests don't depend on a machine-specific font.
    monkeypatch.delenv('KAITI_FONT_PATH', raising=False)


def test_add_header_footer_preserves_page_count_and_draws_footer(make_pdf, tmp_path):
    input_path = make_pdf(n_pages=2)
    output_path = tmp_path / 'output.pdf'

    ahf.add_header_footer(input_path, output_path, header_text='Confidential')

    reader = PdfReader(str(output_path))
    assert len(reader.pages) == 2
    text = reader.pages[0].extract_text()
    assert 'Confidential' in text
    assert '1' in text  # footer page number


def test_add_header_footer_without_header_text(make_pdf, tmp_path):
    input_path = make_pdf()
    output_path = tmp_path / 'output.pdf'

    ahf.add_header_footer(input_path, output_path, header_text=None)

    reader = PdfReader(str(output_path))
    assert len(reader.pages) == 1


def test_main_derives_output_filename(make_pdf, monkeypatch, capsys):
    input_path = make_pdf(name='report.pdf')
    monkeypatch.setattr('sys.argv', ['add_header_footer.py', str(input_path)])

    ahf.main()

    expected_output = input_path.parent / 'report_stamped.pdf'
    assert expected_output.exists()
    captured = capsys.readouterr()
    assert f'Output saved to "{expected_output}"' in captured.out


def test_main_accepts_header_flag_and_positional_in_any_order(make_pdf, monkeypatch):
    input_path = make_pdf(name='report2.pdf')
    monkeypatch.setattr(
        'sys.argv',
        ['add_header_footer.py', '--header-text', 'Draft', str(input_path)],
    )

    ahf.main()

    expected_output = input_path.parent / 'report2_stamped.pdf'
    reader = PdfReader(str(expected_output))
    assert 'Draft' in reader.pages[0].extract_text()


def test_main_raises_for_missing_input(tmp_path, monkeypatch):
    missing = tmp_path / 'missing.pdf'
    monkeypatch.setattr('sys.argv', ['add_header_footer.py', str(missing)])

    with pytest.raises(FileNotFoundError):
        ahf.main()
