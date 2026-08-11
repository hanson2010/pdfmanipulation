from PyPDF2 import PdfReader
import pytest

import sign_with_pfx as swp


@pytest.fixture(autouse=True)
def _no_iosevka_font(monkeypatch):
    # Force the Helvetica fallback so tests don't depend on a machine-specific font.
    monkeypatch.delenv('IOSEVKA_FONT_PATH', raising=False)


def test_sign_pdf_with_pfx_produces_signed_output(make_pdf, make_pfx, make_sig_image, tmp_path):
    input_path = make_pdf()
    output_path = tmp_path / 'output.pdf'
    pfx_path = make_pfx()
    sig_image_path = make_sig_image()

    swp.sign_pdf_with_pfx(
        str(input_path), str(output_path),
        str(pfx_path), None,
        1, 85, 425,
        str(sig_image_path), '2024-01-01 00:00:00',
    )

    assert output_path.exists()
    reader = PdfReader(str(output_path))
    assert len(reader.pages) == 1
    fields = reader.get_fields()
    assert fields is not None and 'Signature' in fields

    # the temporary overlay file must be cleaned up
    assert not (tmp_path / 'output_overlay.pdf').exists()


def test_sign_pdf_with_pfx_supports_password_protected_pfx(make_pdf, make_pfx, make_sig_image, tmp_path):
    input_path = make_pdf()
    output_path = tmp_path / 'output.pdf'
    pfx_path = make_pfx(password='s3cret')
    sig_image_path = make_sig_image()

    swp.sign_pdf_with_pfx(
        str(input_path), str(output_path),
        str(pfx_path), 's3cret',
        1, 85, 425,
        str(sig_image_path), '2024-01-01 00:00:00',
    )

    assert output_path.exists()


def test_sign_pdf_with_pfx_wrong_password_raises(make_pdf, make_pfx, make_sig_image, tmp_path):
    input_path = make_pdf()
    output_path = tmp_path / 'output.pdf'
    pfx_path = make_pfx(password='s3cret')
    sig_image_path = make_sig_image()

    with pytest.raises(ValueError):
        swp.sign_pdf_with_pfx(
            str(input_path), str(output_path),
            str(pfx_path), 'wrong-password',
            1, 85, 425,
            str(sig_image_path), '2024-01-01 00:00:00',
        )


def test_main_requires_pfx_path_env_var(make_pdf, monkeypatch):
    monkeypatch.delenv('PFX_PATH', raising=False)
    monkeypatch.delenv('SIG_IMAGE_PATH', raising=False)
    input_path = make_pdf()
    monkeypatch.setattr('sys.argv', ['sign_with_pfx.py', str(input_path)])

    with pytest.raises(EnvironmentError):
        swp.main()


def test_main_end_to_end_via_env_vars(make_pdf, make_pfx, make_sig_image, monkeypatch):
    input_path = make_pdf(name='contract.pdf')
    pfx_path = make_pfx()
    sig_image_path = make_sig_image()
    monkeypatch.setenv('PFX_PATH', str(pfx_path))
    monkeypatch.setenv('SIG_IMAGE_PATH', str(sig_image_path))
    monkeypatch.setattr(
        'sys.argv',
        ['sign_with_pfx.py', '--timestamp', '2024-01-01 00:00:00', str(input_path)],
    )

    swp.main()

    expected_output = input_path.parent / 'contract_signed.pdf'
    assert expected_output.exists()
