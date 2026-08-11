import datetime

import pikepdf
import pytest
from pikepdf import Array, Dictionary, Name


@pytest.fixture
def make_pdf(tmp_path):
    """Create a minimal valid PDF with blank pages and return its path."""
    def _make(name='input.pdf', n_pages=1, page_size=(612, 792)):
        path = tmp_path / name
        pdf = pikepdf.new()
        for _ in range(n_pages):
            pdf.add_blank_page(page_size=page_size)
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_encrypted_pdf(tmp_path):
    """Create a PDF encrypted with an owner password (openable without a password,
    but restricted/flagged as encrypted) and return its path — the scenario
    `remove_password.py` targets, since it never prompts for a password itself."""
    def _make(name='protected.pdf', owner_password='ownerpw', user_password=''):
        path = tmp_path / name
        pdf = pikepdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        pdf.save(
            path,
            encryption=pikepdf.Encryption(user=user_password, owner=owner_password),
        )
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pfx(tmp_path):
    """Create a self-signed PKCS#12 (.pfx) certificate and return its path."""
    def _make(name='cert.pfx', password=None):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.x509.oid import NameOID

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'Test Signer'),
        ])
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        encryption = (
            serialization.BestAvailableEncryption(password.encode())
            if password else serialization.NoEncryption()
        )
        data = pkcs12.serialize_key_and_certificates(
            name=b'test', key=key, cert=cert, cas=None,
            encryption_algorithm=encryption,
        )
        path = tmp_path / name
        path.write_bytes(data)
        return path
    return _make


def _helvetica_font(pdf):
    """A standard Type1 Helvetica font dict, so PyPDF2 can decode `Tj` text back out
    (with no /Font resource, extracted text comes back as mojibake)."""
    return pdf.make_indirect(
        Dictionary(Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica)
    )


@pytest.fixture
def make_pdf_with_watermark_annotation(tmp_path):
    """PDF with page content plus a standard /Subtype /Watermark annotation
    (what Acrobat's "Add Watermark" feature produces)."""
    def _make(name='watermark_annot.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)
        page.Contents = pdf.make_stream(b'BT /F1 12 Tf 10 10 Td (Body text) Tj ET')
        page.Resources = Dictionary(Font=Dictionary(F1=_helvetica_font(pdf)))
        annot = pdf.make_indirect(
            Dictionary(Type=Name.Annot, Subtype=Name.Watermark, Rect=Array([0, 0, *page_size]))
        )
        page.Annots = Array([annot])
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_ocg_watermark(tmp_path):
    """PDF where the watermark is drawn inside a `/OC .../BDC ... EMC` marked-content
    section tied to an Optional Content Group named "Watermark"."""
    def _make(name='ocg_watermark.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        ocg = pdf.make_indirect(Dictionary(Type=Name.OCG, Name='Watermark'))
        pdf.Root.OCProperties = Dictionary(
            OCGs=Array([ocg]), D=Dictionary(ON=Array([ocg]), OFF=Array())
        )

        content = (
            b'BT /F1 12 Tf 10 10 Td (Body text) Tj ET\n'
            b'q /OC /MC0 BDC BT /F1 24 Tf 10 100 Td (WATERMARK) Tj ET EMC Q'
        )
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(
            Properties=Dictionary(MC0=ocg), Font=Dictionary(F1=_helvetica_font(pdf))
        )
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_unregistered_ocmd_watermark(tmp_path):
    """PDF where the watermark is a generically-named Form XObject whose /OC entry
    is an OCMD (Optional Content Membership Dictionary) wrapping an OCG named
    "Watermark" — but that OCG is never registered in the document's
    /OCProperties catalog entry (real-world generators don't always bother).
    Also barely rotated (~1deg), below the rotation threshold."""
    def _make(name='unregistered_ocmd_watermark.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)
        # deliberately no pdf.Root.OCProperties assignment

        font = _helvetica_font(pdf)
        ocg = Dictionary(Type=Name.OCG, Name='Watermark')
        ocmd = pdf.make_indirect(Dictionary(Type=Name.OCMD, OCGs=ocg))
        watermark_form = pdf.make_stream(
            b'BT /F1 24 Tf 0 0 Td (WATERMARK) Tj ET',
            Type=Name.XObject, Subtype=Name.Form, OC=ocmd,
            BBox=Array([0, 0, 100, 20]), Resources=Dictionary(Font=Dictionary(F1=font)),
        )
        content = (
            b'BT /F1 12 Tf 10 10 Td (Body text) Tj ET\n'
            b'q 0.9998 0.0175 -0.0175 0.9998 50 50 cm /Fm0 Do Q'  # ~1 degree tilt
        )
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(
            XObject=Dictionary(Fm0=watermark_form), Font=Dictionary(F1=font)
        )
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_named_xobject_watermark(tmp_path):
    """PDF where the watermark is a Form XObject named "Watermark", drawn via `Do`
    with no Optional Content wrapper — matched by resource name instead."""
    def _make(name='named_xobject_watermark.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        font = _helvetica_font(pdf)
        watermark_form = pdf.make_stream(
            b'BT /F1 24 Tf 10 100 Td (WATERMARK) Tj ET',
            Type=Name.XObject, Subtype=Name.Form,
            BBox=Array([0, 0, *page_size]), Resources=Dictionary(Font=Dictionary(F1=font)),
        )
        content = (
            b'BT /F1 12 Tf 10 10 Td (Body text) Tj ET\n'
            b'q 1 0 0 1 0 0 cm /Watermark Do Q'
        )
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(
            XObject=Dictionary(Watermark=watermark_form), Font=Dictionary(F1=font)
        )
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_rotated_watermark(tmp_path):
    """PDF where the watermark is a generically-named, untagged Form XObject drawn
    diagonally (rotated `cm`) — mirrors real-world watermarks that carry no name,
    annotation, or OCG tag at all and are only identifiable by their placement."""
    def _make(name='rotated_watermark.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        font = _helvetica_font(pdf)
        # deliberately generic resource name (not "watermark") - only the rotation
        # should mark this as removable.
        watermark_form = pdf.make_stream(
            b'BT /F1 24 Tf 0 0 Td (WATERMARK) Tj ET',
            Type=Name.XObject, Subtype=Name.Form,
            BBox=Array([0, 0, 100, 20]), Resources=Dictionary(Font=Dictionary(F1=font)),
        )
        content = (
            b'BT /F1 12 Tf 10 10 Td (Body text) Tj ET\n'
            b'q 0.7071 0.7071 -0.7071 0.7071 50 50 cm /Fm0 Do Q'
        )
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(
            XObject=Dictionary(Fm0=watermark_form), Font=Dictionary(F1=font)
        )
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_slightly_skewed_image(tmp_path):
    """PDF with a legitimate, mostly axis-aligned image tilted by only ~2 degrees
    (the kind of incidental skew a scanner or PDF generator can introduce) — should
    be kept, not mistaken for a deliberately rotated watermark."""
    def _make(name='slightly_skewed.pdf', page_size=(200, 200), angle_degrees=2):
        import math

        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        image = pdf.make_stream(
            bytes([128]) * 100, Type=Name.XObject, Subtype=Name.Image,
            Width=10, Height=10, ColorSpace=Name.DeviceGray, BitsPerComponent=8,
        )
        theta = math.radians(angle_degrees)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        content = (
            f'q {100 * cos_t} {100 * sin_t} {-100 * sin_t} {100 * cos_t} 50 50 cm '
            f'/Im0 Do Q'
        ).encode()
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(XObject=Dictionary(Im0=image))
        pdf.save(path)
        pdf.close()
        return path
    return _make


def _make_masked_image(pdf, alpha_value, size=(20, 20)):
    """An axis-aligned, untagged Image XObject with a uniform /SMask (alpha channel)
    — mirrors watermark stamps that pre-render their diagonal tilt into pixels
    instead of using a PDF rotation matrix, so no `cm`/name/tag gives them away."""
    w, h = size
    pixel_count = w * h
    smask = pdf.make_stream(
        bytes([alpha_value]) * pixel_count, Type=Name.XObject, Subtype=Name.Image,
        Width=w, Height=h, ColorSpace=Name.DeviceGray, BitsPerComponent=8,
    )
    return pdf.make_stream(
        bytes([100]) * (pixel_count * 3), Type=Name.XObject, Subtype=Name.Image,
        Width=w, Height=h, ColorSpace=Name.DeviceRGB, BitsPerComponent=8, SMask=smask,
    )


@pytest.fixture
def make_pdf_with_transparent_watermark_image(tmp_path):
    """PDF where the watermark is baked into an image's pixels (near-fully
    transparent /SMask), placed with a plain axis-aligned `cm`/`Do` and a generic
    resource name — no rotation matrix, tag, or name to detect it by."""
    def _make(name='transparent_watermark.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        watermark_image = _make_masked_image(pdf, alpha_value=5)  # ~2% opaque
        font = _helvetica_font(pdf)
        content = (
            b'BT /F1 12 Tf 10 10 Td (Body text) Tj ET\n'
            b'q 100 0 0 100 50 50 cm /Im0 Do Q'
        )
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(
            XObject=Dictionary(Im0=watermark_image), Font=Dictionary(F1=font)
        )
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_opaque_masked_image(tmp_path):
    """PDF with a legitimate, fully-opaque masked image (a real photo/graphic can
    have an /SMask too, e.g. for anti-aliased edges) — should be kept."""
    def _make(name='opaque_masked.pdf', page_size=(200, 200)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        image = _make_masked_image(pdf, alpha_value=255)  # fully opaque
        content = b'q 100 0 0 100 50 50 cm /Im0 Do Q'
        page.Contents = pdf.make_stream(content)
        page.Resources = Dictionary(XObject=Dictionary(Im0=image))
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_pdf_with_background_image(tmp_path):
    """PDF with a full-page Image XObject drawn first (a "background"), plus a
    small unrelated image that only covers part of the page."""
    def _make(name='background.pdf', page_size=(200, 100)):
        path = tmp_path / name
        pdf = pikepdf.new()
        page = pdf.add_blank_page(page_size=page_size)

        def make_image(pixel):
            return pdf.make_stream(
                bytes([pixel]) * 100, Type=Name.XObject, Subtype=Name.Image,
                Width=10, Height=10, ColorSpace=Name.DeviceGray, BitsPerComponent=8,
            )

        background = make_image(0)
        small_image = make_image(255)

        page.Resources = Dictionary(
            XObject=Dictionary(Bg=background, Small=small_image),
            Font=Dictionary(F1=_helvetica_font(pdf)),
        )
        w, h = page_size
        content = (
            f'q {w} 0 0 {h} 0 0 cm /Bg Do Q\n'
            f'q 20 0 0 20 5 5 cm /Small Do Q\n'
            'BT /F1 12 Tf 10 10 Td (Body text) Tj ET'
        ).encode()
        page.Contents = pdf.make_stream(content)
        pdf.save(path)
        pdf.close()
        return path
    return _make


@pytest.fixture
def make_sig_image(tmp_path):
    """Create a small PNG signature image and return its path."""
    def _make(name='sig.png', size=(120, 60)):
        from PIL import Image

        path = tmp_path / name
        Image.new('RGB', size, color=(10, 10, 10)).save(path)
        return path
    return _make
