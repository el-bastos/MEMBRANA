"""Lipid type definitions and composition models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LipidCategory(str, Enum):
    GLYCEROPHOSPHOLIPID = "glycerophospholipid"
    SPHINGOLIPID = "sphingolipid"
    STEROL = "sterol"
    GLYCOLIPID = "glycolipid"
    CERAMIDE = "ceramide"
    CUSTOM = "custom"


class GeometricShape(str, Enum):
    CYLINDER = "cylinder"
    CONE = "cone"
    INVERTED_CONE = "inverted_cone"


class LipidType(BaseModel):
    id: str
    name: str
    abbreviation: str
    category: LipidCategory = LipidCategory.GLYCEROPHOSPHOLIPID
    num_tails: int = Field(ge=1, le=4, default=2)
    tail_lengths: list[float] = Field(default_factory=lambda: [1.0, 1.0])
    geometric_shape: GeometricShape = GeometricShape.CYLINDER
    head_color: str = "#4A90D9"
    tail_color: str = "#C8A84E"
    head_radius_factor: float = 1.0
    is_truncated: bool = False
    special_rendering: Optional[str] = None
    tail_kinks: list[list[float]] = Field(default_factory=list)


class LeafletComposition(BaseModel):
    ratios: dict[str, float] = Field(default_factory=dict)


class LipidComposition(BaseModel):
    outer_leaflet: LeafletComposition = Field(
        default_factory=lambda: LeafletComposition(
            ratios={"PC": 0.5, "PE": 0.3, "cholesterol": 0.2}
        )
    )
    inner_leaflet: LeafletComposition = Field(
        default_factory=lambda: LeafletComposition(
            ratios={"PC": 0.5, "PE": 0.3, "cholesterol": 0.2}
        )
    )
    asymmetric: bool = False


# ---------------------------------------------------------------------------
# Default lipid type library
# ---------------------------------------------------------------------------

DEFAULT_LIPID_TYPES: list[LipidType] = [
    # ── Glycerophospholipids (all-trans / saturated) ──
    LipidType(
        id="PC", name="Phosphatidylcholine", abbreviation="PC",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#4A90D9", tail_color="#C8A84E",
    ),
    LipidType(
        id="PE", name="Phosphatidylethanolamine", abbreviation="PE",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#2EAE7A", tail_color="#C8A84E",
    ),
    LipidType(
        id="PS", name="Phosphatidylserine", abbreviation="PS",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#E85D75", tail_color="#C8A84E",
    ),
    LipidType(
        id="PI", name="Phosphatidylinositol", abbreviation="PI",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#9B59B6", tail_color="#C8A84E",
    ),
    LipidType(
        id="PA", name="Phosphatidic acid", abbreviation="PA",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#E67E22", tail_color="#C8A84E",
    ),
    LipidType(
        id="PG", name="Phosphatidylglycerol", abbreviation="PG",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#1ABC9C", tail_color="#C8A84E",
    ),
    # Cardiolipin - 4 tails (saturated)
    LipidType(
        id="CL", name="Cardiolipin", abbreviation="CL",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=4, tail_lengths=[1.0, 1.0, 1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#C0392B", tail_color="#C8A84E",
        head_radius_factor=1.3,
    ),

    # ── Glycerophospholipids (cis / unsaturated, sn-2 kinked at 55%) ──
    LipidType(
        id="cis-PC", name="Phosphatidylcholine (unsaturated)", abbreviation="cis-PC",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#4A90D9", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    LipidType(
        id="cis-PE", name="Phosphatidylethanolamine (unsaturated)", abbreviation="cis-PE",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#2EAE7A", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    LipidType(
        id="cis-PS", name="Phosphatidylserine (unsaturated)", abbreviation="cis-PS",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#E85D75", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    LipidType(
        id="cis-PI", name="Phosphatidylinositol (unsaturated)", abbreviation="cis-PI",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#9B59B6", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    LipidType(
        id="cis-PA", name="Phosphatidic acid (unsaturated)", abbreviation="cis-PA",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#E67E22", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    LipidType(
        id="cis-PG", name="Phosphatidylglycerol (unsaturated)", abbreviation="cis-PG",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#1ABC9C", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    # Cardiolipin (unsaturated) - sn-2 and sn-4 kinked
    LipidType(
        id="cis-CL", name="Cardiolipin (unsaturated)", abbreviation="cis-CL",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=4, tail_lengths=[1.0, 1.0, 1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#C0392B", tail_color="#C8A84E",
        head_radius_factor=1.3,
        tail_kinks=[[], [0.55], [], [0.55]],
    ),

    # ── Sphingolipids (typically saturated) ──
    LipidType(
        id="SM", name="Sphingomyelin", abbreviation="SM",
        category=LipidCategory.SPHINGOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#F39C12", tail_color="#C8A84E",
    ),

    # ── Sterols ──
    LipidType(
        id="cholesterol", name="Cholesterol", abbreviation="Chol",
        category=LipidCategory.STEROL,
        num_tails=1, tail_lengths=[0.6],
        geometric_shape=GeometricShape.CONE,
        head_color="#F1C40F", tail_color="#D4AC0D",
        head_radius_factor=0.6,
        special_rendering="cholesterol",
    ),

    # ── Ceramide (typically saturated) ──
    LipidType(
        id="ceramide", name="Ceramide", abbreviation="Cer",
        category=LipidCategory.CERAMIDE,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#8B4513", tail_color="#C8A84E",
        head_radius_factor=0.7,
    ),

    # ── Glycolipids (all-trans / saturated) ──
    LipidType(
        id="MGDG", name="Monogalactosyldiacylglycerol", abbreviation="MGDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#27AE60", tail_color="#C8A84E",
    ),
    LipidType(
        id="DGDG", name="Digalactosyldiacylglycerol", abbreviation="DGDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#2ECC71", tail_color="#C8A84E",
        head_radius_factor=1.2,
    ),
    LipidType(
        id="MGlcDG", name="Monoglucosyldiacylglycerol", abbreviation="MGlcDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#16A085", tail_color="#C8A84E",
    ),
    LipidType(
        id="DGlcDG", name="Diglucosyldiacylglycerol", abbreviation="DGlcDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#1ABC9C", tail_color="#C8A84E",
        head_radius_factor=1.2,
    ),
    LipidType(
        id="SQDG", name="Sulfoquinovosyldiacylglycerol", abbreviation="SQDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#3498DB", tail_color="#C8A84E",
    ),

    # ── Glycolipids (cis / unsaturated, sn-2 kinked at 55%) ──
    LipidType(
        id="cis-MGDG", name="MGDG (unsaturated)", abbreviation="cis-MGDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CONE,
        head_color="#27AE60", tail_color="#C8A84E",
        tail_kinks=[[], [0.55]],
    ),
    LipidType(
        id="cis-DGDG", name="DGDG (unsaturated)", abbreviation="cis-DGDG",
        category=LipidCategory.GLYCOLIPID,
        num_tails=2, tail_lengths=[1.0, 1.0],
        geometric_shape=GeometricShape.CYLINDER,
        head_color="#2ECC71", tail_color="#C8A84E",
        head_radius_factor=1.2,
        tail_kinks=[[], [0.55]],
    ),

    # ── Lysolipids (saturated) ──
    LipidType(
        id="lysoPC", name="Lysophosphatidylcholine", abbreviation="LysoPC",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=1, tail_lengths=[1.0],
        geometric_shape=GeometricShape.INVERTED_CONE,
        head_color="#85C1E9", tail_color="#C8A84E",
    ),
    LipidType(
        id="lysoPE", name="Lysophosphatidylethanolamine", abbreviation="LysoPE",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=1, tail_lengths=[1.0],
        geometric_shape=GeometricShape.INVERTED_CONE,
        head_color="#82E0AA", tail_color="#C8A84E",
    ),

    # ── Lysolipids (cis / unsaturated) ──
    LipidType(
        id="cis-lysoPC", name="LysoPC (unsaturated)", abbreviation="cis-LysoPC",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=1, tail_lengths=[1.0],
        geometric_shape=GeometricShape.INVERTED_CONE,
        head_color="#85C1E9", tail_color="#C8A84E",
        tail_kinks=[[0.55]],
    ),
    LipidType(
        id="cis-lysoPE", name="LysoPE (unsaturated)", abbreviation="cis-LysoPE",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=1, tail_lengths=[1.0],
        geometric_shape=GeometricShape.INVERTED_CONE,
        head_color="#82E0AA", tail_color="#C8A84E",
        tail_kinks=[[0.55]],
    ),

    # ── Truncated lipids ──
    LipidType(
        id="truncPC", name="Truncated PC", abbreviation="tPC",
        category=LipidCategory.GLYCEROPHOSPHOLIPID,
        num_tails=2, tail_lengths=[1.0, 0.4],
        geometric_shape=GeometricShape.INVERTED_CONE,
        head_color="#5DADE2", tail_color="#C8A84E",
        is_truncated=True,
    ),
]
