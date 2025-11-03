# pdfmanipulation

## Prepare

```bash
pip install -r requirements.txt
```

## Add header (optional) and footer to a PDF file

Footer will always be formated as `–page#–`, where the dashes are unicode `U+2013`.

- **Without header:**

  ```bash
  ./add_header_footer.sh document.pdf
  ```

  Output: `document_stamped.pdf`

- **With header:**

  ```bash
  ./add_header_footer.sh document.pdf "Confidential - Do Not Distribute"
  ```

  Output: `document_stamped.pdf`
