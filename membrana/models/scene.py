"""Top-level scene configuration."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .annotations import AnnotationConfig
from .lipids import LipidComposition, LipidType, DEFAULT_LIPID_TYPES
from .membrane import MembraneConfig
from .modes import PoreModeConfig, RaftModeConfig, ScissorModeConfig
from .proteins import ProteinConfig


class SceneConfig(BaseModel):
    canvas_width: float = Field(default=1200.0, ge=200, le=4000)
    canvas_height: float = Field(default=600.0, ge=200, le=4000)
    background_color: Optional[str] = None

    membrane: MembraneConfig = Field(default_factory=MembraneConfig)
    lipid_types: list[LipidType] = Field(default_factory=lambda: list(DEFAULT_LIPID_TYPES))
    composition: LipidComposition = Field(default_factory=LipidComposition)
    proteins: list[ProteinConfig] = Field(default_factory=list)
    annotations: AnnotationConfig = Field(default_factory=AnnotationConfig)

    scissor_mode: ScissorModeConfig = Field(default_factory=ScissorModeConfig)
    pore_mode: PoreModeConfig = Field(default_factory=PoreModeConfig)
    raft_mode: RaftModeConfig = Field(default_factory=RaftModeConfig)

    show_legend: bool = True
