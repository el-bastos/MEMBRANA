"""Renders membrane background (fill between leaflets)."""

from __future__ import annotations

from ..geometry.curves import ParametricCurve
from ..models.membrane import MembraneConfig
from . import styles
from .svg_builder import _fmt, svg_group, svg_path


def render_membrane_background(
    curve: ParametricCurve,
    config: MembraneConfig,
) -> str:
    """Render the hydrophobic core as a filled region between leaflets."""
    half = config.width / 2.0
    n_samples = 120

    # Sample outer edge
    outer_pts: list[tuple[float, float]] = []
    inner_pts: list[tuple[float, float]] = []

    for i in range(n_samples + 1):
        t = i / n_samples
        if curve.is_closed and i == n_samples:
            t = 0.0  # Close the loop
        cp = curve.sample(t)
        outer_pts.append((cp.x + cp.normal_x * half, cp.y + cp.normal_y * half))
        inner_pts.append((cp.x - cp.normal_x * half, cp.y - cp.normal_y * half))

    # Build path: outer edge forward, inner edge backward
    if not outer_pts:
        return ""

    d = f"M {_fmt(outer_pts[0][0])} {_fmt(outer_pts[0][1])}"
    for px, py in outer_pts[1:]:
        d += f" L {_fmt(px)} {_fmt(py)}"

    # Reverse inner path
    for px, py in reversed(inner_pts):
        d += f" L {_fmt(px)} {_fmt(py)}"
    d += " Z"

    bg = svg_path(
        d,
        fill=config.membrane_color,
        fill_opacity=styles.MEMBRANE_BG_OPACITY,
        stroke="none",
    )

    # Membrane midline (dashed)
    mid_d = f"M {_fmt(outer_pts[0][0] - (outer_pts[0][0] - inner_pts[0][0]) / 2)} {_fmt(outer_pts[0][1] - (outer_pts[0][1] - inner_pts[0][1]) / 2)}"
    midline_pts: list[str] = []
    for i in range(n_samples + 1):
        t = i / n_samples
        if curve.is_closed and i == n_samples:
            t = 0.0
        cp = curve.sample(t)
        midline_pts.append(f"{_fmt(cp.x)} {_fmt(cp.y)}")

    mid_d = f"M {midline_pts[0]}"
    for pt in midline_pts[1:]:
        mid_d += f" L {pt}"

    midline = svg_path(
        mid_d,
        fill="none",
        stroke="#999",
        stroke_width=0.5,
        stroke_dasharray="4,4",
        stroke_opacity=0.4,
    )

    return svg_group([bg, midline], **{"class": "membrane-background"})
