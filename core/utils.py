"""Shared helper utilities for the image converter app."""

from __future__ import annotations

import os
from pathlib import Path

# All supported input/output image formats
SUPPORTED_FORMATS: list[str] = ["JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "ICO", "PDF"]

# Maps PIL format names to file extensions
FORMAT_EXTENSIONS: dict[str, str] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "TIFF": ".tiff",
    "GIF": ".gif",
    "ICO": ".ico",
    "PDF": ".pdf",
}

# Formats that support quality parameter
LOSSY_FORMATS: set[str] = {"JPEG", "WEBP"}


def get_supported_formats() -> list[str]:
    """Return list of all supported output format names."""
    return list(SUPPORTED_FORMATS)


def detect_format(path: str) -> str:
    """Detect the format of an image file from its extension."""
    ext = Path(path).suffix.lower()
    mapping = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP",
        ".bmp": "BMP",
        ".tiff": "TIFF",
        ".tif": "TIFF",
        ".gif": "GIF",
        ".ico": "ICO",
        ".pdf": "PDF",
    }
    return mapping.get(ext, "PNG")


def safe_output_path(src: str, dest_format: str, output_dir: str) -> str:
    """
    Build a unique output file path.
    If a file with the same name already exists, appends _1, _2, etc.
    """
    ext = FORMAT_EXTENSIONS.get(dest_format, ".png")
    stem = Path(src).stem
    base = Path(output_dir) / f"{stem}{ext}"

    if not base.exists():
        return str(base)

    counter = 1
    while True:
        candidate = Path(output_dir) / f"{stem}_{counter}{ext}"
        if not candidate.exists():
            return str(candidate)
        counter += 1


def ensure_dir(directory: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)
