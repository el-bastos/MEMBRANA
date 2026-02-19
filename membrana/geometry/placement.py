"""Lipid placement engine - distributes lipids along parametric curves."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..models.lipids import LeafletComposition, LipidComposition, LipidType
from ..models.membrane import MembraneConfig
from .curves import CurvePoint, ParametricCurve


@dataclass
class LipidInstance:
    """A placed lipid in the membrane."""

    lipid_type_id: str
    x: float
    y: float
    angle: float  # Rotation in radians (normal direction)
    scale: float
    leaflet: str  # "outer" or "inner"
    t: float  # Parameter along curve (for filtering, modes, etc.)


def distribute_types(ratios: dict[str, float], n: int) -> list[str]:
    """Bresenham-style dithering for even lipid type distribution.

    Given ratios like {"PC": 0.6, "PE": 0.2, "Chol": 0.2} and n=50 slots,
    produces an evenly-spaced sequence rather than random clumping.
    """
    if not ratios or n <= 0:
        return []

    # Normalize ratios
    total = sum(ratios.values())
    if total < 1e-10:
        types = list(ratios.keys())
        return [types[i % len(types)] for i in range(n)]

    norm = {k: v / total for k, v in ratios.items()}
    types = sorted(norm.keys(), key=lambda k: -norm[k])

    error = {t: 0.0 for t in types}
    result: list[str] = []

    for _ in range(n):
        for t in types:
            error[t] += norm[t]
        best = max(types, key=lambda t: error[t])
        result.append(best)
        error[best] -= 1.0

    return result


class LipidPlacer:
    """Places lipids along a parametric curve based on composition."""

    def __init__(
        self,
        curve: ParametricCurve,
        config: MembraneConfig,
        composition: LipidComposition,
        lipid_types: dict[str, LipidType],
    ):
        self.curve = curve
        self.config = config
        self.composition = composition
        self.lipid_types = lipid_types

    def place_leaflet(
        self,
        leaflet: str,
        offset_sign: float,
    ) -> list[LipidInstance]:
        """Place lipids for one leaflet.

        offset_sign: +1 for outer leaflet (normal direction),
                    -1 for inner leaflet (anti-normal).
        """
        half_thickness = self.config.width / 2.0 + self.config.leaflet_gap / 2.0
        offset = offset_sign * half_thickness
        spacing = self.config.lipid_base_size + self.config.lipid_spacing

        # Sample the centerline at uniform intervals
        center_points = self.curve.sample_uniform(spacing)

        # Get composition for this leaflet
        if leaflet == "outer":
            comp = self.composition.outer_leaflet
        elif self.composition.asymmetric:
            comp = self.composition.inner_leaflet
        else:
            comp = self.composition.outer_leaflet

        # Distribute lipid types across positions
        type_ids = distribute_types(comp.ratios, len(center_points))

        instances: list[LipidInstance] = []
        for i, cp in enumerate(center_points):
            # Offset along normal
            ox = cp.x + cp.normal_x * offset
            oy = cp.y + cp.normal_y * offset

            # Lipid angle: tails point TOWARD membrane center
            # Outer leaflet: tails in -normal direction (toward center)
            # Inner leaflet: tails in +normal direction (toward center)
            if leaflet == "outer":
                angle = math.atan2(-cp.normal_y, -cp.normal_x)
            else:
                angle = math.atan2(cp.normal_y, cp.normal_x)

            # Calculate t parameter (approximate from index)
            t_param = (i + 0.5) / len(center_points) if center_points else 0.5

            lipid_type_id = type_ids[i] if i < len(type_ids) else list(comp.ratios.keys())[0]

            instances.append(LipidInstance(
                lipid_type_id=lipid_type_id,
                x=ox,
                y=oy,
                angle=angle,
                scale=1.0,
                leaflet=leaflet,
                t=t_param,
            ))

        return instances

    def place_all(self) -> list[LipidInstance]:
        """Place lipids on both leaflets."""
        outer = self.place_leaflet("outer", +1.0)
        inner = self.place_leaflet("inner", -1.0)
        return outer + inner
