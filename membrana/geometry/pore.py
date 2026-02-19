"""Pore geometry for toroidal and barrel-stave pores."""

from __future__ import annotations

import math

from .curves import CurvePoint


def compute_toroidal_pore_lipids(
    center_x: float,
    center_y: float,
    pore_radius: float,
    membrane_width: float,
    num_lipids: int,
) -> list[CurvePoint]:
    """Compute lipid positions along a toroidal pore edge.

    Lipids curve from the outer leaflet through the pore to the inner leaflet,
    forming a half-torus cross-section on each side.
    """
    points: list[CurvePoint] = []
    half_w = membrane_width / 2.0

    # Left edge of pore - semicircle going from outer to inner leaflet
    left_cx = center_x - pore_radius
    half_count = num_lipids // 2

    for i in range(half_count):
        # Angle from top (outer leaflet) to bottom (inner leaflet)
        frac = (i + 0.5) / half_count
        angle = -math.pi / 2 + frac * math.pi  # -pi/2 to +pi/2
        px = left_cx + half_w * math.cos(angle)
        py = center_y + half_w * math.sin(angle)
        # Normal points toward pore center (inward)
        nx = math.cos(angle)
        ny = math.sin(angle)
        points.append(CurvePoint(px, py, nx, ny, math.atan2(ny, nx)))

    # Right edge of pore - semicircle
    right_cx = center_x + pore_radius
    for i in range(num_lipids - half_count):
        frac = (i + 0.5) / (num_lipids - half_count)
        angle = math.pi / 2 - frac * math.pi  # pi/2 to -pi/2
        px = right_cx - half_w * math.cos(angle)
        py = center_y + half_w * math.sin(angle)
        nx = -math.cos(angle)
        ny = -math.sin(angle)
        points.append(CurvePoint(px, py, nx, ny, math.atan2(ny, nx)))

    return points
