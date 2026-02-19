"""Special mode configurations (scissor, pore, raft)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScissorPlacement(BaseModel):
    position_t: float = Field(default=0.5, ge=0.0, le=1.0)
    leaflet: str = "outer"  # "outer" or "inner"


class ScissorModeConfig(BaseModel):
    enabled: bool = False
    enzyme: str = "PLA2"  # PLA1, PLA2, PLC, PLD
    placements: list[ScissorPlacement] = Field(
        default_factory=lambda: [ScissorPlacement(position_t=0.5)]
    )
    scissor_color: str = "#FF0000"
    scissor_size: float = Field(default=20.0, ge=8, le=50)


class PorePlacement(BaseModel):
    position_t: float = Field(default=0.5, ge=0.0, le=1.0)
    pore_type: str = "toroidal"  # "toroidal" or "barrel_stave"


class PoreModeConfig(BaseModel):
    enabled: bool = False
    pore_radius: float = Field(default=30.0, ge=10, le=100)
    num_lipids_in_pore: int = Field(default=8, ge=4, le=20)
    placements: list[PorePlacement] = Field(
        default_factory=lambda: [PorePlacement(position_t=0.5)]
    )
    # Kept for backward compat with saved configs (ignored by renderer)
    pore_type: str = "toroidal"
    position_t: float = Field(default=0.5, ge=0.0, le=1.0)


class RaftPlacement(BaseModel):
    start_t: float = Field(default=0.3, ge=0.0, le=1.0)
    end_t: float = Field(default=0.6, ge=0.0, le=1.0)


class RaftModeConfig(BaseModel):
    enabled: bool = False
    thickness_factor: float = Field(default=1.3, ge=1.0, le=2.0)
    placements: list[RaftPlacement] = Field(
        default_factory=lambda: [RaftPlacement()]
    )
    # Kept for backward compat with saved configs (ignored by renderer)
    start_t: float = Field(default=0.3, ge=0.0, le=1.0)
    end_t: float = Field(default=0.6, ge=0.0, le=1.0)
    cholesterol_enrichment: float = Field(default=0.4, ge=0.0, le=1.0)
    sm_enrichment: float = Field(default=0.3, ge=0.0, le=1.0)
