"""2D affine transform utilities."""

from __future__ import annotations

import math


def transform_str(
    tx: float = 0.0,
    ty: float = 0.0,
    angle_deg: float = 0.0,
    scale: float = 1.0,
) -> str:
    """Build an SVG transform attribute string."""
    parts: list[str] = []
    if tx != 0.0 or ty != 0.0:
        parts.append(f"translate({tx:.2f},{ty:.2f})")
    if angle_deg != 0.0:
        parts.append(f"rotate({angle_deg:.2f})")
    if scale != 1.0:
        parts.append(f"scale({scale:.4f})")
    return " ".join(parts)
