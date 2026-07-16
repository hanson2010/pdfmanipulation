#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import List


def split_markdown(content: str, max_lines: int = 500) -> List[str]:
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
            raise RuntimeError("pymupdf4llm not installed. Please install it first.")
    elif file_ext in (".docx", ".xlsx", ".xls", "pptx", "ppt"):
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            result = md.convert(str(input_path))
            return result.text_content
        except ImportError:
            raise RuntimeError("markitdown not installed. Please install it first with 'pip install markitdown[all]'.")
    elif file_ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"):
        try:
            import easyocr
            # Initialize EasyOCR reader for English, Simplified Chinese, and Traditional Chinese
            reader = easyocr.Reader(['en', 'ch_sim', 'ch_tra'])
            results = reader.readtext(str(input_path), detail=0)
            text = "\n".join(results)
            return f"# {input_path.name}\n\n{text}"
        except ImportError:
            raise RuntimeError("easyocr not installed. Please install it first.")
    else:
        raise RuntimeError(f"Unsupported file type {file_ext}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert documents to Markdown.")
    parser.add_argument("input_pattern", help="Input file or wildcard pattern (quote patterns like '*.pdf')")
    parser.add_argument("-o", "--output-dir", help="Output directory (default: same as input file directory)")
    
    args = parser.parse_args()

    pattern_path = Path(args.input_pattern)

    if pattern_path.is_absolute():
        input_paths = list(pattern_path.parent.glob(pattern_path.name))
    else:
        input_paths = list(Path.cwd().glob(args.input_pattern))
    
    if input_paths:
        print(f"Found {len(input_paths)} file(s) matching '{args.input_pattern}':")
        for p in input_paths:
            print(f"  - {p}")
        for input_path in input_paths:
            if input_path.is_file():
                try:
                    if args.output_dir:
                        output_dir = Path(args.output_dir)
                    else:
                        output_dir = input_path.parent
                    
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
                except Exception as e:
                    print(f"Error processing {input_path}: {e}", file=sys.stderr)
            else:
                print(f"Skipping {input_path}: not a file", file=sys.stderr)
    else:
        print(f"No files found matching {args.input_pattern}", file=sys.stderr)


if __name__ == "__main__":
    main()
