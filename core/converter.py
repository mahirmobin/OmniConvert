"""
Core image conversion logic.

Handles:
  - Single image format conversion (JPEG, PNG, WEBP, BMP, TIFF, GIF, ICO)
  - Multiple images → single merged PDF
  - DPI embedding and quality control during save
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from PIL import Image, UnidentifiedImageError

from core.dpi import change_dpi
from core.resizer import resize_image
from core.utils import (
    LOSSY_FORMATS,
    ensure_dir,
    safe_output_path,
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class ConversionResult:
    """Lightweight result object returned by each conversion operation."""

    def __init__(self, success: bool, src: str, dest: str, message: str) -> None:
        self.success = success
        self.src = src
        self.dest = dest
        self.message = message

    def __repr__(self) -> str:  # pragma: no cover
        status = "OK" if self.success else "ERR"
        return f"ConversionResult({status}: {self.src} → {self.dest})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _open_image(path: str) -> Image.Image:
    """Open an image file and return a PIL Image in a safe mode."""
    img = Image.open(path)
    img.load()  # force decode so errors surface here
    return img


def _prepare_image(
    img: Image.Image,
    dest_format: str,
    width: int | None,
    height: int | None,
    maintain_aspect: bool,
    dpi: int | None,
) -> Image.Image:
    """Apply resize and DPI changes; convert colour mode as needed."""
    # Resize if dimensions are specified
    if width or height:
        img = resize_image(img, width, height, maintain_aspect)

    # DPI
    if dpi:
        img = change_dpi(img, dpi)

    # Convert colour mode for target format
    if dest_format == "JPEG":
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
    elif dest_format == "ICO":
        img = img.convert("RGBA")
    elif dest_format in ("PNG", "WEBP", "TIFF"):
        pass  # These formats handle most modes natively
    elif dest_format == "BMP":
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
    elif dest_format == "GIF":
        img = img.convert("P", palette=Image.ADAPTIVE)

    return img


def _save_kwargs(dest_format: str, quality: int, dpi: int | None) -> dict:
    """Build keyword arguments for PIL Image.save()."""
    kwargs: dict = {}
    if dest_format in LOSSY_FORMATS:
        kwargs["quality"] = max(1, min(95, quality))
    if dpi:
        kwargs["dpi"] = (dpi, dpi)
    if dest_format == "TIFF":
        kwargs["compression"] = "tiff_lzw"
    return kwargs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_image(
    src: str,
    dest_format: str,
    output_dir: str,
    quality: int = 85,
    width: int | None = None,
    height: int | None = None,
    maintain_aspect: bool = True,
    dpi: int | None = None,
) -> ConversionResult:
    """
    Convert a single image to the target format.

    Args:
        src: Absolute path to the source image.
        dest_format: Target format string (e.g. "JPEG", "PNG").
        output_dir: Directory to write the converted file.
        quality: 1–95, used for lossy formats (JPEG, WEBP).
        width: Target width in pixels; None = unchanged.
        height: Target height in pixels; None = unchanged.
        maintain_aspect: Preserve aspect ratio when resizing.
        dpi: Target DPI; None = preserve original.

    Returns:
        ConversionResult with success flag and message.
    """
    dest_path = ""
    try:
        ensure_dir(output_dir)
        dest_path = safe_output_path(src, dest_format, output_dir)

        img = _open_image(src)
        img = _prepare_image(img, dest_format, width, height, maintain_aspect, dpi)
        kwargs = _save_kwargs(dest_format, quality, dpi)

        img.save(dest_path, format=dest_format, **kwargs)

        return ConversionResult(
            success=True,
            src=src,
            dest=dest_path,
            message=f"Saved → {Path(dest_path).name}",
        )

    except UnidentifiedImageError:
        return ConversionResult(
            success=False, src=src, dest=dest_path,
            message=f"Cannot read image: {Path(src).name}",
        )
    except Exception as exc:  # noqa: BLE001
        return ConversionResult(
            success=False, src=src, dest=dest_path,
            message=f"Error ({Path(src).name}): {exc}",
        )


def images_to_pdf(
    image_paths: list[str],
    output_path: str,
    quality: int = 85,
    width: int | None = None,
    height: int | None = None,
    maintain_aspect: bool = True,
    dpi: int | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> ConversionResult:
    """
    Merge multiple images into a single PDF.

    Args:
        image_paths: Ordered list of image file paths.
        output_path: Full path for the output PDF file.
        quality: JPEG quality used internally by Pillow when embedding.
        width: Optional resize width.
        height: Optional resize height.
        maintain_aspect: Preserve aspect ratio during resize.
        dpi: Optional DPI override.
        progress_cb: Optional callback(current, total, message).

    Returns:
        ConversionResult for the PDF as a whole.
    """
    pil_images: list[Image.Image] = []
    total = len(image_paths)

    try:
        ensure_dir(str(Path(output_path).parent))

        for i, path in enumerate(image_paths, start=1):
            if progress_cb:
                progress_cb(i, total, f"Loading {Path(path).name}…")

            img = _open_image(path)
            img = _prepare_image(img, "JPEG", width, height, maintain_aspect, dpi)

            # PDF requires RGB
            if img.mode != "RGB":
                img = img.convert("RGB")

            pil_images.append(img)

        if not pil_images:
            return ConversionResult(
                success=False, src="", dest=output_path,
                message="No valid images to convert to PDF.",
            )

        first, rest = pil_images[0], pil_images[1:]
        first.save(output_path, format="PDF", save_all=True, append_images=rest)

        return ConversionResult(
            success=True, src=", ".join(Path(p).name for p in image_paths),
            dest=output_path,
            message=f"PDF created → {Path(output_path).name} ({total} page(s))",
        )

    except Exception as exc:  # noqa: BLE001
        return ConversionResult(
            success=False, src="", dest=output_path,
            message=f"PDF error: {exc}",
        )


def batch_convert(
    image_paths: list[str],
    dest_format: str,
    output_dir: str,
    quality: int = 85,
    width: int | None = None,
    height: int | None = None,
    maintain_aspect: bool = True,
    dpi: int | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> list[ConversionResult]:
    """
    Convert multiple images, calling progress_cb after each file.

    Returns:
        List of ConversionResult, one per input file.
    """
    results: list[ConversionResult] = []
    total = len(image_paths)

    for i, path in enumerate(image_paths, start=1):
        if progress_cb:
            progress_cb(i, total, f"Converting {Path(path).name}…")

        result = convert_image(
            src=path,
            dest_format=dest_format,
            output_dir=output_dir,
            quality=quality,
            width=width,
            height=height,
            maintain_aspect=maintain_aspect,
            dpi=dpi,
        )
        results.append(result)

    return results
