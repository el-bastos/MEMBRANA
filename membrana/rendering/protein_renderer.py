"""Renders protein shapes as SVG fragments.

Each protein is drawn centered at origin spanning the membrane width.
The caller wraps in a <g transform="..."> for positioning.
"""

from __future__ import annotations

from ..models.proteins import ProteinConfig, ProteinKind
from . import styles
from .svg_builder import (
    _fmt,
    svg_circle,
    svg_ellipse,
    svg_group,
    svg_line,
    svg_path,
    svg_rect,
    svg_text,
)


def render_protein(
    protein: ProteinConfig,
    membrane_width: float,
) -> str:
    """Render a protein at origin. Membrane spans from -membrane_width/2 to +membrane_width/2."""
    kind = protein.kind
    if kind == ProteinKind.SINGLE_PASS_TM:
        return _render_single_pass(protein, membrane_width)
    elif kind == ProteinKind.MULTI_PASS_TM:
        return _render_multi_pass(protein, membrane_width)
    elif kind == ProteinKind.BETA_BARREL:
        return _render_beta_barrel(protein, membrane_width)
    elif kind == ProteinKind.PERIPHERAL:
        return _render_peripheral(protein, membrane_width)
    elif kind == ProteinKind.GPI_ANCHORED:
        return _render_gpi_anchored(protein, membrane_width)
    elif kind == ProteinKind.ION_CHANNEL:
        return _render_ion_channel(protein, membrane_width)
    elif kind == ProteinKind.ATP_SYNTHASE:
        return _render_atp_synthase(protein, membrane_width)
    else:
        return _render_single_pass(protein, membrane_width)


def _render_single_pass(p: ProteinConfig, mw: float) -> str:
    """Single alpha-helix spanning the bilayer."""
    elements: list[str] = []
    half = mw / 2
    w = p.width * 0.3
    # TM helix
    elements.append(svg_rect(
        -w / 2, -half, w, mw,
        fill=p.color, stroke="#333", stroke_width=0.8, rx=w / 4,
    ))
    # Extra-membrane domains
    domain_r = w * 0.8
    elements.append(svg_ellipse(0, -half - domain_r * 0.6, domain_r, domain_r * 0.6,
                                fill=p.color, stroke="#333", stroke_width=0.6, fill_opacity=0.7))
    elements.append(svg_ellipse(0, half + domain_r * 0.6, domain_r, domain_r * 0.6,
                                fill=p.color, stroke="#333", stroke_width=0.6, fill_opacity=0.7))
    if p.label:
        elements.append(svg_text(p.label, 0, -half - domain_r * 1.5,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})


def _render_multi_pass(p: ProteinConfig, mw: float) -> str:
    """Multiple TM helices connected by loops."""
    elements: list[str] = []
    half = mw / 2
    n = max(2, p.num_passes)
    total_w = p.width
    helix_w = total_w / (n * 1.5)
    spacing = total_w / n
    start_x = -(n - 1) * spacing / 2

    for i in range(n):
        x = start_x + i * spacing
        elements.append(svg_rect(
            x - helix_w / 2, -half, helix_w, mw,
            fill=p.color, stroke="#333", stroke_width=0.6, rx=helix_w / 4,
        ))
        # Loops connecting helices
        if i < n - 1:
            nx = start_x + (i + 1) * spacing
            loop_y = -half if i % 2 == 0 else half
            loop_dir = -1 if i % 2 == 0 else 1
            d = (f"M {_fmt(x + helix_w / 2)} {_fmt(loop_y)} "
                 f"C {_fmt(x + helix_w / 2)} {_fmt(loop_y + loop_dir * 10)}, "
                 f"{_fmt(nx - helix_w / 2)} {_fmt(loop_y + loop_dir * 10)}, "
                 f"{_fmt(nx - helix_w / 2)} {_fmt(loop_y)}")
            elements.append(svg_path(d, fill="none", stroke=p.color, stroke_width=1.2))

    if p.label:
        elements.append(svg_text(p.label, 0, -half - 15,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})


def _render_beta_barrel(p: ProteinConfig, mw: float) -> str:
    """Beta-barrel (e.g., porins)."""
    elements: list[str] = []
    half = mw / 2
    w = p.width * 0.5
    # Barrel shape: rounded rectangle
    elements.append(svg_rect(
        -w / 2, -half, w, mw,
        fill=p.color, stroke="#333", stroke_width=1.0,
        rx=w / 2, fill_opacity=0.8,
    ))
    # Vertical stripes to suggest beta-sheets
    n_strands = 6
    strand_spacing = w / (n_strands + 1)
    for i in range(1, n_strands + 1):
        sx = -w / 2 + i * strand_spacing
        elements.append(svg_line(
            sx, -half + 3, sx, half - 3,
            stroke="#333", stroke_width=0.4, stroke_opacity=0.4,
        ))
    # Central pore
    elements.append(svg_ellipse(0, 0, w * 0.15, half * 0.4,
                                fill=styles.PORE_WATER_COLOR, stroke="#333",
                                stroke_width=0.5))
    if p.label:
        elements.append(svg_text(p.label, 0, -half - 10,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})


def _render_peripheral(p: ProteinConfig, mw: float) -> str:
    """Peripheral protein sitting on one surface."""
    elements: list[str] = []
    half = mw / 2
    w = p.width * 0.4
    h = p.height * 0.3
    if p.leaflet == "inner":
        cy = half + h * 0.5
    else:
        cy = -half - h * 0.5
    elements.append(svg_ellipse(0, cy, w, h,
                                fill=p.color, stroke="#333", stroke_width=0.8))
    if p.label:
        label_y = cy - h - 5 if p.leaflet != "inner" else cy + h + 12
        elements.append(svg_text(p.label, 0, label_y,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})


def _render_gpi_anchored(p: ProteinConfig, mw: float) -> str:
    """GPI-anchored protein on outer leaflet."""
    elements: list[str] = []
    half = mw / 2
    blob_r = p.width * 0.2
    # Anchor line from outer leaflet to protein
    elements.append(svg_line(0, -half, 0, -half - blob_r * 2.5,
                             stroke=p.color, stroke_width=1.5, stroke_dasharray="3,2"))
    # Small lipid-like anchor at membrane
    elements.append(svg_circle(0, -half, 2.5, fill=p.color, stroke="#333", stroke_width=0.5))
    # Protein blob
    elements.append(svg_ellipse(0, -half - blob_r * 3.5, blob_r, blob_r * 0.7,
                                fill=p.color, stroke="#333", stroke_width=0.8))
    if p.label:
        elements.append(svg_text(p.label, 0, -half - blob_r * 5,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})


def _render_ion_channel(p: ProteinConfig, mw: float) -> str:
    """Ion channel: hourglass shape."""
    elements: list[str] = []
    half = mw / 2
    outer_w = p.width * 0.5
    inner_w = p.width * 0.12

    # Hourglass outline
    d = (
        f"M {_fmt(-outer_w / 2)} {_fmt(-half)} "
        f"C {_fmt(-outer_w / 2)} {_fmt(-half * 0.3)}, "
        f"{_fmt(-inner_w / 2)} {_fmt(-2)}, "
        f"{_fmt(-inner_w / 2)} {_fmt(0)} "
        f"C {_fmt(-inner_w / 2)} {_fmt(2)}, "
        f"{_fmt(-outer_w / 2)} {_fmt(half * 0.3)}, "
        f"{_fmt(-outer_w / 2)} {_fmt(half)} "
        f"L {_fmt(outer_w / 2)} {_fmt(half)} "
        f"C {_fmt(outer_w / 2)} {_fmt(half * 0.3)}, "
        f"{_fmt(inner_w / 2)} {_fmt(2)}, "
        f"{_fmt(inner_w / 2)} {_fmt(0)} "
        f"C {_fmt(inner_w / 2)} {_fmt(-2)}, "
        f"{_fmt(outer_w / 2)} {_fmt(-half * 0.3)}, "
        f"{_fmt(outer_w / 2)} {_fmt(-half)} "
        f"Z"
    )
    elements.append(svg_path(d, fill=p.color, stroke="#333", stroke_width=0.8,
                             fill_opacity=0.75))
    # Pore
    elements.append(svg_ellipse(0, 0, inner_w * 0.8, 3,
                                fill=styles.PORE_WATER_COLOR, stroke="none"))
    if p.label:
        elements.append(svg_text(p.label, 0, -half - 10,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})


def _render_atp_synthase(p: ProteinConfig, mw: float) -> str:
    """ATP synthase: Fo ring in membrane + stalk + F1 head above."""
    elements: list[str] = []
    half = mw / 2
    ring_w = p.width * 0.35
    ring_h = mw * 0.9

    # Fo ring (barrel spanning membrane)
    elements.append(svg_rect(
        -ring_w / 2, -half, ring_w, ring_h,
        fill=p.color, stroke="#333", stroke_width=0.8,
        rx=ring_w / 3, fill_opacity=0.8,
    ))
    # Central pore in Fo
    elements.append(svg_ellipse(0, 0, ring_w * 0.15, half * 0.3,
                                fill="#fff", stroke="#333", stroke_width=0.4, fill_opacity=0.5))

    # Stalk
    stalk_w = ring_w * 0.2
    stalk_h = p.height * 0.25
    elements.append(svg_rect(
        -stalk_w / 2, -half - stalk_h, stalk_w, stalk_h,
        fill=p.color, stroke="#333", stroke_width=0.6, rx=stalk_w / 3,
    ))

    # F1 head (sphere/ellipse)
    f1_r = ring_w * 0.6
    f1_y = -half - stalk_h - f1_r * 0.7
    elements.append(svg_ellipse(0, f1_y, f1_r, f1_r * 0.65,
                                fill=p.color, stroke="#333", stroke_width=0.8,
                                fill_opacity=0.9))
    # Label inside F1
    elements.append(svg_text("F₁", 0, f1_y + 4, font_size=8, text_anchor="middle",
                             font_family=styles.LABEL_FONT_FAMILY, fill="#fff",
                             font_weight="bold"))
    # Fo label
    elements.append(svg_text("Fₒ", 0, 4, font_size=7, text_anchor="middle",
                             font_family=styles.LABEL_FONT_FAMILY, fill="#fff",
                             font_weight="bold"))

    if p.label:
        elements.append(svg_text(p.label, 0, f1_y - f1_r - 8,
                                 font_size=9, text_anchor="middle",
                                 font_family=styles.LABEL_FONT_FAMILY, fill="#333"))
    return svg_group(elements, **{"class": f"protein protein-{p.id}"})
