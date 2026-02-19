"""Renders annotations: labels, legend, scale bars, arrows, scissors."""

from __future__ import annotations

import math

from ..geometry.curves import ParametricCurve
from ..models.annotations import AnnotationConfig
from ..models.lipids import LipidComposition, LipidType
from ..models.membrane import MembraneConfig
from ..models.modes import ScissorModeConfig
from . import styles
from .svg_builder import (
    _fmt,
    svg_circle,
    svg_group,
    svg_line,
    svg_path,
    svg_rect,
    svg_text,
)


def render_annotations(
    config: AnnotationConfig,
    curve: ParametricCurve,
    membrane: MembraneConfig,
    canvas_width: float,
    canvas_height: float,
) -> str:
    """Render all annotations."""
    elements: list[str] = []

    # Compartment labels
    for label in config.compartment_labels:
        if not label.text:
            continue
        if label.position == "top":
            x, y = canvas_width / 2, 25
        elif label.position == "bottom":
            x, y = canvas_width / 2, canvas_height - 15
        elif label.position == "left":
            x, y = 20, canvas_height / 2
        else:
            x, y = canvas_width - 20, canvas_height / 2

        elements.append(svg_text(
            label.text, x, y,
            font_size=label.font_size,
            font_family=styles.LABEL_FONT_FAMILY,
            text_anchor="middle",
            fill=label.color,
            font_style="italic",
        ))

    # Leaflet labels
    if config.show_leaflet_labels:
        cp_mid = curve.sample(0.5)
        half = membrane.width / 2
        elements.append(svg_text(
            config.outer_leaflet_label,
            cp_mid.x, cp_mid.y + cp_mid.normal_y * (half + 20),
            font_size=10, font_family=styles.LABEL_FONT_FAMILY,
            text_anchor="middle", fill="#666", font_style="italic",
        ))
        elements.append(svg_text(
            config.inner_leaflet_label,
            cp_mid.x, cp_mid.y - cp_mid.normal_y * (half + 20),
            font_size=10, font_family=styles.LABEL_FONT_FAMILY,
            text_anchor="middle", fill="#666", font_style="italic",
        ))

    # Scale bar
    if config.show_scale_bar:
        bar_w = config.scale_bar_nm * 20  # 20 SVG units per nm (approximate)
        bar_x = canvas_width - bar_w - 30
        bar_y = canvas_height - 40
        elements.append(svg_line(bar_x, bar_y, bar_x + bar_w, bar_y,
                                 stroke="#333", stroke_width=2))
        elements.append(svg_line(bar_x, bar_y - 4, bar_x, bar_y + 4,
                                 stroke="#333", stroke_width=2))
        elements.append(svg_line(bar_x + bar_w, bar_y - 4, bar_x + bar_w, bar_y + 4,
                                 stroke="#333", stroke_width=2))
        elements.append(svg_text(
            f"{config.scale_bar_nm:.0f} nm",
            bar_x + bar_w / 2, bar_y - 8,
            font_size=10, font_family=styles.LABEL_FONT_FAMILY,
            text_anchor="middle", fill="#333",
        ))

    # Thickness markers
    if config.show_thickness_markers:
        cp_start = curve.sample(0.05)
        half = membrane.width / 2
        bx = cp_start.x
        top_y = cp_start.y + cp_start.normal_y * half
        bot_y = cp_start.y - cp_start.normal_y * half
        # Bracket
        elements.append(svg_line(bx - 15, top_y, bx - 15, bot_y,
                                 stroke="#555", stroke_width=1))
        elements.append(svg_line(bx - 18, top_y, bx - 12, top_y,
                                 stroke="#555", stroke_width=1))
        elements.append(svg_line(bx - 18, bot_y, bx - 12, bot_y,
                                 stroke="#555", stroke_width=1))
        elements.append(svg_text(
            "~4 nm", bx - 22, (top_y + bot_y) / 2 + 3,
            font_size=8, font_family=styles.LABEL_FONT_FAMILY,
            text_anchor="end", fill="#555",
        ))

    # Flip-flop arrows
    for arrow in config.flip_flop_arrows:
        if not arrow.enabled:
            continue
        cp = curve.sample(arrow.position_t)
        half = membrane.width / 2
        if arrow.direction == "outward":
            y1 = cp.y - cp.normal_y * half * 0.3
            y2 = cp.y + cp.normal_y * half * 0.3
        else:
            y1 = cp.y + cp.normal_y * half * 0.3
            y2 = cp.y - cp.normal_y * half * 0.3

        # Curved arrow
        ctrl_x = cp.x + 15
        d = (f"M {_fmt(cp.x)} {_fmt(y1)} "
             f"C {_fmt(ctrl_x)} {_fmt(y1)}, "
             f"{_fmt(ctrl_x)} {_fmt(y2)}, "
             f"{_fmt(cp.x)} {_fmt(y2)}")
        elements.append(svg_path(d, fill="none", stroke=arrow.color,
                                 stroke_width=1.5, marker_end="url(#arrowhead)"))

    if not elements:
        return ""
    return svg_group(elements, **{"class": "annotations"})


def render_legend(
    lipid_types: dict[str, LipidType],
    composition: LipidComposition,
    x: float,
    y: float,
) -> str:
    """Render color-coded legend for active lipid types."""
    # Collect active types from composition
    active_ids: set[str] = set()
    for lid, ratio in composition.outer_leaflet.ratios.items():
        if ratio > 0:
            active_ids.add(lid)
    if composition.asymmetric:
        for lid, ratio in composition.inner_leaflet.ratios.items():
            if ratio > 0:
                active_ids.add(lid)

    if not active_ids:
        return ""

    elements: list[str] = []
    ss = styles.LEGEND_SWATCH_SIZE
    pad = styles.LEGEND_PADDING
    line_h = ss + 6

    # Background box
    n = len(active_ids)
    box_w = 130
    box_h = n * line_h + pad * 2
    elements.append(svg_rect(
        x, y, box_w, box_h,
        fill="white", stroke="#ccc", stroke_width=0.5,
        rx=4, fill_opacity=0.9,
    ))

    for i, lid in enumerate(sorted(active_ids)):
        lt = lipid_types.get(lid)
        if not lt:
            continue
        row_y = y + pad + i * line_h

        # Color swatch
        elements.append(svg_circle(
            x + pad + ss / 2, row_y + ss / 2,
            ss / 2,
            fill=lt.head_color, stroke="#333", stroke_width=0.5,
        ))
        # Label
        elements.append(svg_text(
            lt.abbreviation,
            x + pad + ss + 6, row_y + ss / 2 + 4,
            font_size=styles.LEGEND_FONT_SIZE,
            font_family=styles.LABEL_FONT_FAMILY,
            fill="#333",
        ))

    return svg_group(elements, **{"class": "legend"})


def render_scissor_icon(x: float, y: float, angle_deg: float, color: str,
                        size: float = 20.0, enzyme: str = "PLA2") -> str:
    """Render a scissor icon with enzyme label at the given position.

    The blades point in the +x direction (right at angle=0).
    The scene renderer rotates so blades face toward the membrane.
    """
    s = size / 2
    ring_r = s * 0.24
    elements = [
        # Upper half: handle ring → pivot → blade tip (V shape)
        svg_path(
            f"M {_fmt(-s * 0.85)} {_fmt(-s * 0.4)} "
            f"L {_fmt(0)} {_fmt(0)} "
            f"L {_fmt(s)} {_fmt(s * 0.3)}",
            fill="none", stroke=color, stroke_width=2.0,
            stroke_linecap="round", stroke_linejoin="round",
        ),
        # Lower half: handle ring → pivot → blade tip (V shape, mirror)
        svg_path(
            f"M {_fmt(-s * 0.85)} {_fmt(s * 0.4)} "
            f"L {_fmt(0)} {_fmt(0)} "
            f"L {_fmt(s)} {_fmt(-s * 0.3)}",
            fill="none", stroke=color, stroke_width=2.0,
            stroke_linecap="round", stroke_linejoin="round",
        ),
        # Finger rings
        svg_circle(-s * 0.85, -s * 0.4, ring_r,
                   fill="none", stroke=color, stroke_width=1.4),
        svg_circle(-s * 0.85, s * 0.4, ring_r,
                   fill="none", stroke=color, stroke_width=1.4),
        # Pivot screw
        svg_circle(0, 0, 1.6, fill=color, stroke="none"),
    ]
    # Enzyme label (offset to the handle side so it doesn't overlap blades)
    elements.append(svg_text(
        enzyme, -s * 0.4, -s * 0.8,
        font_size=max(8, size * 0.4),
        font_family=styles.LABEL_FONT_FAMILY,
        text_anchor="middle", fill=color,
        font_weight="bold",
    ))
    inner = svg_group(elements, **{"class": "scissor-icon"})
    return f'<g transform="translate({_fmt(x)},{_fmt(y)}) rotate({_fmt(angle_deg)})">{inner}</g>'
