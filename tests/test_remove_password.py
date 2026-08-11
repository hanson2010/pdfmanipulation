import pikepdf
import pytest

import remove_password as rp


def test_remove_password_strips_encryption(make_encrypted_pdf, tmp_path):
    input_path = make_encrypted_pdf()
    with pikepdf.open(input_path) as pdf:
        assert pdf.is_encrypted

    output_path = tmp_path / 'output.pdf'
    rp.remove_password(input_path, output_path)

    with pikepdf.open(output_path) as pdf:
        assert not pdf.is_encrypted
        assert len(pdf.pages) == 1


def test_main_derives_output_filename_and_prints_it(make_encrypted_pdf, monkeypatch, capsys):
    input_path = make_encrypted_pdf(name='secret.pdf')
    monkeypatch.setattr('sys.argv', ['remove_password.py', str(input_path)])

    rp.main()

    expected_output = input_path.parent / 'secret_decrypted.pdf'
    assert expected_output.exists()
    with pikepdf.open(expected_output) as pdf:
        assert not pdf.is_encrypted

    captured = capsys.readouterr()
    assert f'Output saved to "{expected_output}"' in captured.out


def test_main_raises_for_missing_input(tmp_path, monkeypatch):
    missing = tmp_path / 'missing.pdf'
    monkeypatch.setattr('sys.argv', ['remove_password.py', str(missing)])

    with pytest.raises(FileNotFoundError):
        rp.main()
