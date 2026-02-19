"""Membrane configuration models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MembraneShape(str, Enum):
    LINEAR = "linear"
    CIRCULAR = "circular"
    ELLIPTICAL = "elliptical"
    CRISTAE = "cristae"
    BEZIER = "bezier"


class MembraneConfig(BaseModel):
    shape: MembraneShape = MembraneShape.LINEAR
    # Dimensions (SVG units)
    length: float = Field(default=800.0, ge=100, le=3000)
    width: float = Field(default=60.0, ge=20, le=200)
    # Circular
    radius: float = Field(default=200.0, ge=50, le=800)
    # Elliptical
    ellipse_rx: float = Field(default=250.0, ge=50, le=800)
    ellipse_ry: float = Field(default=150.0, ge=50, le=800)
    # Cristae
    cristae_width: float = Field(default=80.0, ge=30, le=300)
    cristae_depth: float = Field(default=200.0, ge=50, le=600)
    cristae_count: int = Field(default=1, ge=1, le=10)
    cristae_spacing: float = Field(default=120.0, ge=40, le=400)
    # Lipid sizing
    lipid_base_size: float = Field(default=10.0, ge=4, le=40)
    lipid_spacing: float = Field(default=0.5, ge=-8, le=20)
    tail_length_factor: float = Field(default=0.9, ge=0.2, le=1.0)
    leaflet_gap: float = Field(default=0.0, ge=-20, le=40)
    # Bézier
    bezier_points: list[list[float]] = Field(
        default_factory=lambda: [[200, 300], [450, 250], [750, 350], [1000, 300]]
    )
    bezier_handles: list[list[list[float] | None]] = Field(default_factory=list)
    bezier_knot_modes: list[str] = Field(default_factory=list)
    # Display mode
    show_geometric_shapes: bool = False
    show_kinks: bool = True
    show_head_stroke: bool = True
    # 3D depth effect (stacked rows of heads behind the front row)
    show_3d: bool = False
    depth_rows: int = Field(default=5, ge=2, le=8)
    row_spacing: float = Field(default=6.0, ge=2, le=20)
    # Membrane background color (hydrophobic core fill)
    membrane_color: str = "#FDEBD0"
