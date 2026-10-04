"""
PDF Studio Module — Powers the PDF and Image sequence builder.

Uses PyMuPDF (fitz) to precisely render thumbnails and reliably merge
mixed lists of PDF files and Image files.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from core.utils import ensure_dir


def render_pdf_preview(file_path: str, page_num: int = 0, size: tuple[int, int] = (120, 150)) -> Image.Image:
    """
    Render a specific page of a PDF or read an image file natively,
    returning a nicely sized PIL Image thumbnail for the UI.
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path_obj.suffix.lower()

    if ext == ".pdf":
        doc: fitz.Document | None = None
        try:
            doc = fitz.open(file_path)
            if page_num >= len(doc):
                page_num = len(doc) - 1
            if page_num < 0:
                raise ValueError("Page number cannot be negative.")

            page = doc.load_page(page_num)
            px = page.get_pixmap(dpi=72)
            
            # Use safe robust unpacking compatible with older and newer fitz
            if px.alpha:
                img = Image.frombytes("RGBA", (px.width, px.height), px.samples)
            else:
                img = Image.frombytes("RGB", (px.width, px.height), px.samples)

        finally:
            if doc:
                doc.close()
    else:
        # Normal image
        img = Image.open(file_path).convert("RGB")

    # Resize cleanly keeping aspect ratio 
    img.thumbnail(size, Image.Resampling.LANCZOS)
    return img


def merge_to_pdf(file_paths: list[str], output_path: str, resolution: int = 300) -> None:
    """
    Combine an ordered list of mixed files (Images and PDFs) into a single PDF.

    Images are physically converted to PDF streams at the given resolution.
    Existing PDFs are directly appended (lossless).
    """
    if not file_paths:
        raise ValueError("No files provided to merge.")

    ensure_dir(str(Path(output_path).parent))
    target_doc = fitz.open()

    try:
        for idx, path in enumerate(file_paths):
            ext = Path(path).suffix.lower()
            if ext == ".pdf":
                source_doc = fitz.open(path)
                try:
                    target_doc.insert_pdf(source_doc)
                finally:
                    source_doc.close()
            else:
                # Convert Image to PDF
                # Open with fitz or Pillow? fitz is extremely fast for standard imgs.
                img_doc = fitz.open(path)
                try:
                    pdf_bytes = img_doc.convert_to_pdf()
                    temp_pdf = fitz.open("pdf", pdf_bytes)
                    target_doc.insert_pdf(temp_pdf)
                    temp_pdf.close()
                finally:
                    img_doc.close()

        # Save the combined document
        target_doc.save(output_path, garbage=4, deflate=True)

    finally:
        target_doc.close()

