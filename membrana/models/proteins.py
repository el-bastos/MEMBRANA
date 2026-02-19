"""Protein configuration models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProteinKind(str, Enum):
    SINGLE_PASS_TM = "single_pass_tm"
    MULTI_PASS_TM = "multi_pass_tm"
    BETA_BARREL = "beta_barrel"
    PERIPHERAL = "peripheral"
    GPI_ANCHORED = "gpi_anchored"
    ION_CHANNEL = "ion_channel"
    ATP_SYNTHASE = "atp_synthase"


class ProteinConfig(BaseModel):
    id: str
    kind: ProteinKind = ProteinKind.SINGLE_PASS_TM
    label: Optional[str] = None
    color: str = "#8B5CF6"
    position_t: float = Field(ge=0.0, le=1.0, default=0.5)
    width: float = Field(default=40.0, ge=10, le=200)
    height: float = Field(default=80.0, ge=10, le=300)
    num_passes: int = Field(default=1, ge=1, le=12)
    leaflet: str = "both"
