"""Image resize logic with optional aspect ratio preservation."""

from __future__ import annotations

from PIL import Image


def resize_image(
    img: Image.Image,
    width: int | None,
    height: int | None,
    maintain_aspect: bool,
) -> Image.Image:
    """
    Resize a PIL Image.

    Args:
        img: Source PIL Image.
        width: Target width in pixels, or None to determine from height.
        height: Target height in pixels, or None to determine from width.
        maintain_aspect: If True, scale proportionally using the given dimension(s).

    Returns:
        Resized PIL Image.

    Raises:
        ValueError: If both width and height are None.
    """
    if width is None and height is None:
        raise ValueError("At least one of width or height must be specified.")

    orig_w, orig_h = img.size

    if maintain_aspect:
        if width and height:
            # Fit within the bounding box while preserving ratio
            ratio = min(width / orig_w, height / orig_h)
            new_w = max(1, round(orig_w * ratio))
            new_h = max(1, round(orig_h * ratio))
        elif width:
            ratio = width / orig_w
            new_w = width
            new_h = max(1, round(orig_h * ratio))
        else:
            ratio = height / orig_h  # type: ignore[operator]
            new_h = height  # type: ignore[assignment]
            new_w = max(1, round(orig_w * ratio))
    else:
        new_w = width or orig_w
        new_h = height or orig_h

    return img.resize((new_w, new_h), Image.LANCZOS)
