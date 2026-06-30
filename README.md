# pdfmanipulation

## Prepare

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Install Tesseract (for image OCR)

For image-to-markdown conversion to work, you need to install Tesseract OCR on your system:

- **Ubuntu/Debian:**
  ```bash
  sudo apt install tesseract-ocr
  ```

- **macOS (Homebrew):**
  ```bash
  brew install tesseract
  ```

- **Windows:**
  Download from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract) and add to PATH.

## Add header (optional) and footer to a PDF file

Footer will always be formated as `–page#–`, where the dashes are unicode `U+2013`.

Set `VENV_PYTHON_PATH` and `KAITI_FONT_PATH` in `scripts/add_header_footer.sh`.

- **Without header:**

  ```bash
  ./scripts/add_header_footer.sh document.pdf
  ```

  Output: `document_stamped.pdf`

- **With header:**

  ```bash
  ./scripts/add_header_footer.sh document.pdf "Confidential - Do Not Distribute"
  ```

  Output: `document_stamped.pdf`

## Sign a PDF with PFX certificate, signature image, and timestamp

Adds a visible signature image and a timestamp string at a designated page and position, then digitally signs the PDF with a PFX/P12 certificate.

### Configuration

Set the following variables in `scripts/sign_with_pfx.sh`:

| Variable | Description |
|----------|-------------|
| `VENV_PYTHON_PATH` | Path to venv Python interpreter |
| `PFX_PATH` | Path to PFX/P12 certificate file |
| `SIG_IMAGE_PATH` | Path to signature image (PNG/JPG) |
| `IOSEVKA_FONT_PATH` | Path to font file for timestamp text |

If the PFX file is password-protected and no `--password` is provided, the program will prompt for it interactively.

### Usage

- **Basic usage:**

  ```bash
  ./scripts/sign_with_pfx.sh document.pdf
  ```

  Output: `document_signed.pdf`

- **With all options:**

  ```bash
  ./scripts/sign_with_pfx.sh document.pdf \
    --password mypassword \
    --page 2 \
    --x 85 \
    --y 425 \
    --timestamp "2026-04-21 14:30:00"
  ```

  Output: `document_signed.pdf`

- **Options:**

  | Option | Description | Default |
  |--------|-------------|---------|
  | `--password` | PFX password (prompted if needed) | None |
  | `--page` | Page number to sign (1-based) | 1 |
  | `--x` | X coordinate in pt from left edge | 85 (~30mm) |
  | `--y` | Y coordinate in pt from top edge | 425 (~150mm) |
  | `--timestamp` | Timestamp string to display | current date/time |

## Convert files to Markdown

Convert PDFs, DOCX, DOC, and diagram images to Markdown. If the output exceeds 500 lines, it will be split into multiple files at the nearest Markdown header.

### Usage

```bash
./scripts/convert_anything_to_md.sh input.pdf
./scripts/convert_anything_to_md.sh input.docx
./scripts/convert_anything_to_md.sh input.png
./scripts/convert_anything_to_md.sh input.pdf /path/to/output/dir
```

**Supported formats:**
- `.pdf` - PDF documents
- `.docx` - Microsoft Word (modern)
- `.doc` - Microsoft Word (legacy)
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp` - Images (requires Tesseract OCR)

**Output:**
- If output ≤ 500 lines: `input.md`
- If output > 500 lines: `input_part1.md`, `input_part2.md`, etc.

## Strip modification dates from a PDF

Strips modification dates from PDF metadata.

### Usage

```bash
./scripts/strip_moddate.sh document.pdf
```

**Output:** `document_stripped.pdf`
