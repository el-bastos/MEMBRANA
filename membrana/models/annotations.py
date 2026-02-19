"""Annotation configuration models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CompartmentLabel(BaseModel):
    text: str = ""
    position: str = "top"  # "top", "bottom", "left", "right"
    font_size: float = 14.0
    color: str = "#333333"


class FlipFlopArrow(BaseModel):
    enabled: bool = False
    position_t: float = Field(default=0.5, ge=0.0, le=1.0)
    direction: str = "outward"  # "outward" or "inward"
    color: str = "#E74C3C"


class AnnotationConfig(BaseModel):
    compartment_labels: list[CompartmentLabel] = Field(default_factory=list)
    show_scale_bar: bool = False
    scale_bar_nm: float = 5.0
    show_thickness_markers: bool = False
    flip_flop_arrows: list[FlipFlopArrow] = Field(default_factory=list)
    show_leaflet_labels: bool = False
    outer_leaflet_label: str = "Outer leaflet"
    inner_leaflet_label: str = "Inner leaflet"
