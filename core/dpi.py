"""DPI manipulation for PIL Images."""

from __future__ import annotations

from PIL import Image


def change_dpi(img: Image.Image, dpi: int) -> Image.Image:
    """
    Return a copy of the image with updated DPI metadata.

    Note: This changes only the embedded DPI tag — it does NOT
    resample or physically resize the pixel data.

    Args:
        img: Source PIL Image.
        dpi: Target DPI value (e.g. 72, 150, 300, 600).

    Returns:
        PIL Image with DPI info attribute set.
    """
    if dpi <= 0:
        raise ValueError(f"DPI must be a positive integer, got {dpi}.")

    # PIL stores DPI in .info dict; we copy the image so the caller's
    # original is untouched, then inject the new DPI.
    out = img.copy()
    out.info["dpi"] = (dpi, dpi)
    return out
