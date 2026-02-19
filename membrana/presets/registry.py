"""Preset registry: built-in membrane configurations."""

from __future__ import annotations

from ..models.annotations import AnnotationConfig, CompartmentLabel
from ..models.lipids import DEFAULT_LIPID_TYPES, LeafletComposition, LipidComposition
from ..models.membrane import MembraneConfig, MembraneShape
from ..models.scene import SceneConfig


class PresetRegistry:
    def __init__(self):
        self._presets: dict[str, SceneConfig] = {}
        self._register_defaults()

    def _register_defaults(self):
        self._presets["plasma_membrane"] = SceneConfig(
            membrane=MembraneConfig(shape=MembraneShape.LINEAR, length=900, width=65),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"PC": 0.40, "SM": 0.25, "cholesterol": 0.25, "PE": 0.10}
                ),
                inner_leaflet=LeafletComposition(
                    ratios={"PE": 0.35, "PS": 0.20, "PI": 0.10, "PC": 0.20, "cholesterol": 0.15}
                ),
                asymmetric=True,
            ),
            annotations=AnnotationConfig(
                compartment_labels=[
                    CompartmentLabel(text="Extracellular", position="top"),
                    CompartmentLabel(text="Cytoplasm", position="bottom"),
                ],
                show_leaflet_labels=True,
            ),
        )

        self._presets["mito_imm"] = SceneConfig(
            membrane=MembraneConfig(
                shape=MembraneShape.CRISTAE,
                cristae_width=80, cristae_depth=200, cristae_count=2, cristae_spacing=100,
                width=55, lipid_base_size=10,
            ),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"PC": 0.35, "PE": 0.34, "CL": 0.18, "PI": 0.08, "PS": 0.05}
                ),
                inner_leaflet=LeafletComposition(
                    ratios={"PC": 0.35, "PE": 0.34, "CL": 0.18, "PI": 0.08, "PS": 0.05}
                ),
            ),
            annotations=AnnotationConfig(
                compartment_labels=[
                    CompartmentLabel(text="IMS", position="top"),
                    CompartmentLabel(text="Matrix", position="bottom"),
                ],
            ),
        )

        self._presets["vesicle"] = SceneConfig(
            membrane=MembraneConfig(shape=MembraneShape.CIRCULAR, radius=150, width=50,
                                    lipid_base_size=10),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"PC": 0.50, "PE": 0.25, "cholesterol": 0.15, "SM": 0.10}
                ),
            ),
        )

        self._presets["bacterial_om"] = SceneConfig(
            membrane=MembraneConfig(shape=MembraneShape.LINEAR, length=800, width=60),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"PE": 0.60, "PG": 0.25, "CL": 0.15}
                ),
                inner_leaflet=LeafletComposition(
                    ratios={"PE": 0.60, "PG": 0.25, "CL": 0.15}
                ),
            ),
            annotations=AnnotationConfig(
                compartment_labels=[
                    CompartmentLabel(text="Periplasm", position="top"),
                    CompartmentLabel(text="Cytoplasm", position="bottom"),
                ],
            ),
        )

        self._presets["thylakoid"] = SceneConfig(
            membrane=MembraneConfig(shape=MembraneShape.ELLIPTICAL,
                                    ellipse_rx=250, ellipse_ry=120, width=50,
                                    lipid_base_size=10),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"MGDG": 0.50, "DGDG": 0.25, "SQDG": 0.10, "PG": 0.15}
                ),
            ),
            annotations=AnnotationConfig(
                compartment_labels=[
                    CompartmentLabel(text="Stroma", position="top"),
                    CompartmentLabel(text="Lumen", position="bottom"),
                ],
            ),
        )

        self._presets["er_membrane"] = SceneConfig(
            membrane=MembraneConfig(shape=MembraneShape.LINEAR, length=800, width=55),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"PC": 0.55, "PE": 0.25, "PI": 0.10, "PS": 0.05, "cholesterol": 0.05}
                ),
            ),
            annotations=AnnotationConfig(
                compartment_labels=[
                    CompartmentLabel(text="ER Lumen", position="top"),
                    CompartmentLabel(text="Cytoplasm", position="bottom"),
                ],
            ),
        )

        # Custom: blank starting point for user to build anything
        self._presets["custom"] = SceneConfig(
            membrane=MembraneConfig(shape=MembraneShape.LINEAR, length=800, width=60),
            lipid_types=list(DEFAULT_LIPID_TYPES),
            composition=LipidComposition(
                outer_leaflet=LeafletComposition(
                    ratios={"PC": 1.0}
                ),
            ),
        )

    def get(self, preset_id: str) -> SceneConfig | None:
        return self._presets.get(preset_id)

    def list_summaries(self) -> list[dict]:
        return [
            {"id": k, "name": k.replace("_", " ").title()}
            for k in self._presets
        ]
