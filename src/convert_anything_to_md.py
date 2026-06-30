#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def split_markdown(content: str, max_lines: int = 500) -> list[str]:
    lines = content.splitlines(keepends=True)
    if len(lines) <= max_lines:
        return [content]
    
    chunks = []
    current_chunk = []
    last_header_pos = 0  # Position of last header in current chunk
    waiting_for_header = False
    
    for i, line in enumerate(lines):
        current_chunk.append(line)
        
        if line.strip().startswith("#"):
            last_header_pos = len(current_chunk)
            if waiting_for_header and last_header_pos > 0:
                # Split before this header
                split_pos = last_header_pos - 1
                chunks.append("".join(current_chunk[:split_pos]))
                current_chunk = current_chunk[split_pos:]
                last_header_pos = 1  # The header is now at position 1 in new chunk
                waiting_for_header = False
        
        # Check if we need to split
        if len(current_chunk) > max_lines:
            if waiting_for_header:
                # Still waiting, split every max_lines after we hit max_lines
                if len(current_chunk) % max_lines == 0:
                    chunks.append("".join(current_chunk[:max_lines]))
                    current_chunk = current_chunk[max_lines:]
                    last_header_pos = 0
            else:
                if last_header_pos > 0:
                    # We have a previous header - don't split right after it
                    if last_header_pos < len(current_chunk):
                        # Split before the last header
                        split_pos = last_header_pos - 1
                        chunks.append("".join(current_chunk[:split_pos]))
                        current_chunk = current_chunk[split_pos:]
                        last_header_pos = 1  # Header is now at pos 1 in new chunk
                    else:
                        # Header is at the end, which is bad - just split at max_lines
                        chunks.append("".join(current_chunk[:max_lines]))
                        current_chunk = current_chunk[max_lines:]
                        last_header_pos = 0
                else:
                    # No header found yet, start waiting for next header
                    waiting_for_header = True
    
    if current_chunk:
        chunks.append("".join(current_chunk))
    
    return chunks


def convert_file(input_path: Path) -> str:
    file_ext = input_path.suffix.lower()
    if file_ext == ".pdf":
        try:
            import pymupdf4llm
            return pymupdf4llm.to_markdown(str(input_path))
        except ImportError:
            print("Error: pymupdf4llm not installed. Please install it first.", file=sys.stderr)
            sys.exit(1)
    elif file_ext == ".docx":
        try:
            import mammoth
            with open(str(input_path), "rb") as docx_file:
                result = mammoth.convert_to_markdown(docx_file)
                return result.value
        except ImportError:
            print("Error: mammoth not installed. Please install it first.", file=sys.stderr)
            sys.exit(1)
    elif file_ext == ".doc":
        try:
            from docx2txt import process
            text = process(str(input_path))
            return f"# {input_path.name}\n\n{text}"
        except ImportError:
            print("Error: docx2txt not installed. Please install it first.", file=sys.stderr)
            sys.exit(1)
    elif file_ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"):
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(str(input_path))
            text = pytesseract.image_to_string(img)
            return f"# {input_path.name}\n\n{text}"
        except ImportError:
            print("Error: Pillow and pytesseract not installed. Please install them first.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unsupported file type {file_ext}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: convert_anything_to_md.py <input_file> [output_dir]", file=sys.stderr)
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.parent
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_content = convert_file(input_path)
    chunks = split_markdown(markdown_content)
    
    base_name = input_path.stem
    if len(chunks) == 1:
        output_file = output_dir / f"{base_name}.md"
        output_file.write_text(markdown_content, encoding="utf-8")
        print(f"Written to {output_file}")
    else:
        for i, chunk in enumerate(chunks, 1):
            output_file = output_dir / f"{base_name}_part{i}.md"
            output_file.write_text(chunk, encoding="utf-8")
            print(f"Written to {output_file}")


if __name__ == "__main__":
    main()
