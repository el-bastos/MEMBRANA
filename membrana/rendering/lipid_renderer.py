"""Renders individual lipid molecules as SVG fragments.

Each lipid is drawn at the origin. The head is shifted to negative y
(outward from membrane), tails extend in +y direction (toward membrane center).
The (0,0) point represents the leaflet surface position.
The caller wraps in a <g transform="..."> for positioning and rotation.
"""

from __future__ import annotations

import math

from ..models.lipids import GeometricShape, LipidType
from . import styles
from .svg_builder import _fmt, svg_circle, svg_group, svg_path, svg_polygon, svg_rect


def _wavy_tail_d(
    start_x: float,
    start_y: float,
    length: float,
    amplitude: float,
    segments: int = 3,
    kinks: list[float] | None = None,
) -> str:
    """SVG path `d` for a wavy acyl chain (cubic Bezier waves).

    If *kinks* is provided, inserts a smooth elbow bend at each
    fractional position (0-1) to represent cis double-bond kinks.
    """
    if not kinks:
        # Fast path: no kinks
        seg_len = length / segments
        d = f"M {_fmt(start_x)} {_fmt(start_y)}"
        y = start_y
        for s in range(segments):
            direction = 1.0 if s % 2 == 0 else -1.0
            cy1 = y + seg_len * 0.33
            cy2 = y + seg_len * 0.66
            end_y = y + seg_len
            cx1 = start_x + direction * amplitude
            cx2 = start_x - direction * amplitude
            d += (
                f" C {_fmt(cx1)} {_fmt(cy1)},"
                f" {_fmt(cx2)} {_fmt(cy2)},"
                f" {_fmt(start_x)} {_fmt(end_y)}"
            )
            y = end_y
        return d

    # Kinked path: wavy section up to the first kink, then straight
    # angled segments after each cis bond (textbook representation).
    sorted_kinks = sorted(k for k in kinks if 0.0 < k < 1.0)
    if not sorted_kinks:
        return _wavy_tail_d(start_x, start_y, length, amplitude, segments)

    # Each cis bond bends the chain direction by ~30°
    bend = math.radians(30)

    # Build segment boundaries from kink positions
    boundaries = [0.0] + sorted_kinks + [1.0]

    # First section: wavy (like a normal saturated tail)
    first_len = (boundaries[1] - boundaries[0]) * length
    n_wave_segs = max(1, round(segments * (boundaries[1] - boundaries[0])))
    seg_len = first_len / n_wave_segs

    d = f"M {_fmt(start_x)} {_fmt(start_y)}"
    y = start_y
    for s in range(n_wave_segs):
        direction = 1.0 if s % 2 == 0 else -1.0
        cy1 = y + seg_len * 0.33
        cy2 = y + seg_len * 0.66
        end_y = y + seg_len
        cx1 = start_x + direction * amplitude
        cx2 = start_x - direction * amplitude
        d += (
            f" C {_fmt(cx1)} {_fmt(cy1)},"
            f" {_fmt(cx2)} {_fmt(cy2)},"
            f" {_fmt(start_x)} {_fmt(end_y)}"
        )
        y = end_y

    # Remaining sections: straight lines at bent angles
    x = start_x
    angle = 0.0
    for i in range(1, len(boundaries) - 1):
        angle += bend
        seg_len_i = (boundaries[i + 1] - boundaries[i]) * length
        dx = seg_len_i * math.sin(angle)
        dy = seg_len_i * math.cos(angle)
        x += dx
        y += dy
        d += f" L {_fmt(x)} {_fmt(y)}"

    return d


def render_schematic(
    lipid_type: LipidType,
    base_size: float = 12.0,
    membrane_half_width: float = 30.0,
    show_kinks: bool = True,
    show_head_stroke: bool = True,
) -> str:
    """Schematic mode: circle headgroup + wavy tails.

    (0, 0) = leaflet surface position.
    Head center is at (0, -head_r) so the head sits outside the membrane.
    Tails start at (0, 0) and extend in +y toward the membrane center.
    Heads are drawn last so they appear in front of tails.
    """
    scale = base_size / 12.0
    elements: list[str] = []

    head_r = 4.5 * scale * lipid_type.head_radius_factor

    # Head center is offset outward by head_r
    head_cy = -head_r
    head_stroke = "#333" if show_head_stroke else "none"
    head_sw = styles.LIPID_STROKE_WIDTH if show_head_stroke else 0

    if lipid_type.special_rendering == "cholesterol":
        # Cholesterol: short tail first, then ring structure, then OH circle on top
        ring_w = 5.0 * scale
        ring_h = membrane_half_width * 0.5

        # 1. Short flexible tail (behind everything)
        tail_start = ring_h
        remaining = membrane_half_width - ring_h
        tail_len = remaining * (lipid_type.tail_lengths[0] if lipid_type.tail_lengths else 0.6)
        if tail_len > 2:
            d = _wavy_tail_d(0, tail_start, tail_len, 1.5 * scale, segments=2)
            elements.append(svg_path(
                d,
                fill="none",
                stroke=lipid_type.tail_color,
                stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
                stroke_linecap="round",
            ))

        # 2. Rigid ring structure (middle)
        elements.append(svg_rect(
            -ring_w / 2, 0,
            ring_w, ring_h,
            fill=lipid_type.tail_color,
            stroke="#555",
            stroke_width=styles.LIPID_STROKE_WIDTH,
            rx=1.5 * scale,
        ))

        # 3. OH circle head (in front)
        oh_r = head_r * 0.6
        elements.append(svg_circle(
            0, -oh_r, oh_r,
            fill=lipid_type.head_color,
            stroke=head_stroke,
            stroke_width=head_sw,
        ))
    else:
        # Standard phospholipid: tails first, then head on top

        # Tails start at (0, 0) = leaflet surface, extend toward membrane center
        num_tails = lipid_type.num_tails
        tail_base_len = membrane_half_width  # Fill the full half-width
        wave_amp = 2.2 * scale

        def _tail_kinks(i: int) -> list[float] | None:
            if not show_kinks or not lipid_type.tail_kinks:
                return None
            if i < len(lipid_type.tail_kinks) and lipid_type.tail_kinks[i]:
                return lipid_type.tail_kinks[i]
            return None

        if num_tails == 1:
            tl = lipid_type.tail_lengths[0] if lipid_type.tail_lengths else 1.0
            tail_len = tail_base_len * tl
            d = _wavy_tail_d(0, 0, tail_len, wave_amp, kinks=_tail_kinks(0))
            elements.append(svg_path(
                d,
                fill="none",
                stroke=lipid_type.tail_color,
                stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
                stroke_linecap="round",
            ))
            # Head on top
            elements.append(svg_circle(
                0, head_cy, head_r,
                fill=lipid_type.head_color,
                stroke=head_stroke,
                stroke_width=head_sw,
            ))
        elif num_tails == 2:
            gap = 3.0 * scale
            for i, tx in enumerate([-gap / 2, gap / 2]):
                tl = lipid_type.tail_lengths[i] if i < len(lipid_type.tail_lengths) else 1.0
                tail_len = tail_base_len * tl
                d = _wavy_tail_d(tx, 0, tail_len, wave_amp, kinks=_tail_kinks(i))
                elements.append(svg_path(
                    d,
                    fill="none",
                    stroke=lipid_type.tail_color,
                    stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
                    stroke_linecap="round",
                ))
            # Head on top
            elements.append(svg_circle(
                0, head_cy, head_r,
                fill=lipid_type.head_color,
                stroke=head_stroke,
                stroke_width=head_sw,
            ))
        elif num_tails == 3:
            gap = 2.8 * scale
            positions = [-gap, 0, gap]
            for i, tx in enumerate(positions):
                tl = lipid_type.tail_lengths[i] if i < len(lipid_type.tail_lengths) else 1.0
                tail_len = tail_base_len * tl
                d = _wavy_tail_d(tx, 0, tail_len, wave_amp * 0.8, kinks=_tail_kinks(i))
                elements.append(svg_path(
                    d,
                    fill="none",
                    stroke=lipid_type.tail_color,
                    stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
                    stroke_linecap="round",
                ))
            # Head on top
            elements.append(svg_circle(
                0, head_cy, head_r,
                fill=lipid_type.head_color,
                stroke=head_stroke,
                stroke_width=head_sw,
            ))
        elif num_tails >= 4:
            # Cardiolipin: two phosphatidic acid moieties linked by glycerol
            head_gap = 6.0 * scale

            # 1. Tails first (behind heads)
            tail_gap = 2.2 * scale
            positions = [
                -head_gap / 2 - tail_gap / 2,
                -head_gap / 2 + tail_gap / 2,
                head_gap / 2 - tail_gap / 2,
                head_gap / 2 + tail_gap / 2,
            ]
            for i, tx in enumerate(positions):
                tl = lipid_type.tail_lengths[i] if i < len(lipid_type.tail_lengths) else 1.0
                tail_len = tail_base_len * tl
                d = _wavy_tail_d(tx, 0, tail_len, wave_amp * 0.6, kinks=_tail_kinks(i))
                elements.append(svg_path(
                    d,
                    fill="none",
                    stroke=lipid_type.tail_color,
                    stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
                    stroke_linecap="round",
                ))

            # 2. Two PA headgroups (in front)
            hr = head_r * 0.75
            elements.append(svg_circle(
                -head_gap / 2, head_cy, hr,
                fill=lipid_type.head_color,
                stroke=head_stroke,
                stroke_width=head_sw,
            ))
            elements.append(svg_circle(
                head_gap / 2, head_cy, hr,
                fill=lipid_type.head_color,
                stroke=head_stroke,
                stroke_width=head_sw,
            ))
            # Bridging glycerol backbone (line between heads)
            bridge_y = head_cy
            from .svg_builder import svg_line
            elements.append(svg_line(
                -head_gap / 2 + hr, bridge_y,
                head_gap / 2 - hr, bridge_y,
                stroke="#333",
                stroke_width=styles.LIPID_STROKE_WIDTH * 1.2,
            ))
            # Central phosphate dot
            elements.append(svg_circle(
                0, bridge_y, head_r * 0.3,
                fill="#CC5555",
                stroke="#333",
                stroke_width=styles.LIPID_STROKE_WIDTH * 0.8,
            ))

    class_name = f"lipid lipid-{lipid_type.id}"
    return svg_group(elements, **{"class": class_name})


def render_geometric(
    lipid_type: LipidType,
    base_size: float = 12.0,
    membrane_half_width: float = 30.0,
    show_kinks: bool = True,
    show_head_stroke: bool = True,
) -> str:
    """Geometric mode: cone / cylinder / inverted cone outline with
    schematic head + tails rendered inside.
    """
    scale = base_size / 12.0
    elements: list[str] = []

    total_h = membrane_half_width + 4.5 * scale * lipid_type.head_radius_factor
    head_w = 10.0 * scale
    tail_w = 10.0 * scale

    shape = lipid_type.geometric_shape
    if shape == GeometricShape.CONE:
        head_w = 6.0 * scale
        tail_w = 14.0 * scale
    elif shape == GeometricShape.INVERTED_CONE:
        head_w = 14.0 * scale
        tail_w = 6.0 * scale

    head_r = 4.5 * scale * lipid_type.head_radius_factor
    head_cy = -head_r

    # Trapezoid outline: from head top to tail bottom
    pts = (
        f"{_fmt(-head_w / 2)},{_fmt(head_cy - head_r)} "
        f"{_fmt(head_w / 2)},{_fmt(head_cy - head_r)} "
        f"{_fmt(tail_w / 2)},{_fmt(membrane_half_width)} "
        f"{_fmt(-tail_w / 2)},{_fmt(membrane_half_width)}"
    )
    elements.append(svg_polygon(
        pts,
        fill=lipid_type.head_color,
        fill_opacity=styles.GEO_FILL_OPACITY,
        stroke=styles.GEO_STROKE_COLOR,
        stroke_width=styles.GEO_STROKE_WIDTH,
    ))

    # Tails inside outline (drawn before head so head is in front)
    tail_len = membrane_half_width * 0.8
    wave_amp = 1.8 * scale
    num_tails = lipid_type.num_tails

    def _geo_kinks(i: int) -> list[float] | None:
        if not show_kinks or not lipid_type.tail_kinks:
            return None
        if i < len(lipid_type.tail_kinks) and lipid_type.tail_kinks[i]:
            return lipid_type.tail_kinks[i]
        return None

    if num_tails == 1:
        d = _wavy_tail_d(0, 0, tail_len, wave_amp, segments=2, kinks=_geo_kinks(0))
        elements.append(svg_path(
            d,
            fill="none",
            stroke=lipid_type.tail_color,
            stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
            stroke_linecap="round",
        ))
    else:
        gap = min(3.0 * scale, tail_w * 0.6 / num_tails)
        start_x = -gap * (num_tails - 1) / 2
        for i in range(num_tails):
            tx = start_x + i * gap
            tl = lipid_type.tail_lengths[i] if i < len(lipid_type.tail_lengths) else 1.0
            d = _wavy_tail_d(tx, 0, tail_len * tl, wave_amp * 0.8, segments=2, kinks=_geo_kinks(i))
            elements.append(svg_path(
                d,
                fill="none",
                stroke=lipid_type.tail_color,
                stroke_width=styles.LIPID_TAIL_STROKE_WIDTH * scale,
                stroke_linecap="round",
            ))

    # Headgroup circle inside outline (on top of tails)
    geo_head_stroke = "#333" if show_head_stroke else "none"
    geo_head_sw = styles.LIPID_STROKE_WIDTH if show_head_stroke else 0
    elements.append(svg_circle(
        0, head_cy, min(head_w * 0.45, head_r),
        fill=lipid_type.head_color,
        stroke=geo_head_stroke,
        stroke_width=geo_head_sw,
    ))

    class_name = f"lipid lipid-{lipid_type.id} geometric"
    return svg_group(elements, **{"class": class_name})


def render_lipid(
    lipid_type: LipidType,
    base_size: float = 12.0,
    geometric_mode: bool = False,
    membrane_half_width: float = 30.0,
    show_kinks: bool = True,
    show_head_stroke: bool = True,
) -> str:
    """Render a lipid in the appropriate mode."""
    if geometric_mode:
        return render_geometric(lipid_type, base_size, membrane_half_width, show_kinks, show_head_stroke)
    return render_schematic(lipid_type, base_size, membrane_half_width, show_kinks, show_head_stroke)
