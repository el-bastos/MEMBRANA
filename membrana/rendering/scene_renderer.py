"""Top-level scene renderer: orchestrates membrane + lipids + proteins + annotations."""

from __future__ import annotations

import math
import re

from ..geometry.curves import (
    CircularCurve,
    EllipticalCurve,
    LinearCurve,
    ParametricCurve,
    build_cristae_curve,
    build_spline_curve,
)
from ..geometry.placement import LipidInstance, LipidPlacer
from ..geometry.pore import compute_toroidal_pore_lipids
from ..geometry.transforms import transform_str
from ..models.lipids import LipidType
from ..models.membrane import MembraneConfig, MembraneShape
from ..models.scene import SceneConfig
from .annotation_renderer import (
    render_annotations,
    render_legend,
    render_scissor_icon,
)
from .lipid_renderer import render_lipid
from .membrane_renderer import render_membrane_background
from .protein_renderer import render_protein
from .svg_builder import SVGBuilder, svg_circle, svg_line, svg_path, svg_rect, svg_group, svg_ellipse


def _lighten_color(hex_color: str, factor: float) -> str:
    """Blend *hex_color* toward white by *factor* (0 = no change, 1 = white)."""
    m = re.match(r"#?([0-9a-fA-F]{6})", hex_color)
    if not m:
        return hex_color
    r = int(m.group(1)[0:2], 16)
    g = int(m.group(1)[2:4], 16)
    b = int(m.group(1)[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


class SceneRenderer:
    """Composes the complete SVG scene from a SceneConfig."""

    def render(self, config: SceneConfig) -> str:
        svg = SVGBuilder(config.canvas_width, config.canvas_height)

        # Arrow marker definition for flip-flop arrows
        svg.add_def(
            '<marker id="arrowhead" markerWidth="8" markerHeight="6" '
            'refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
            '<polygon points="0 0, 8 3, 0 6" fill="#E74C3C"/>'
            '</marker>'
        )

        # Background
        if config.background_color:
            svg.add(svg_rect(
                0, 0, config.canvas_width, config.canvas_height,
                fill=config.background_color,
            ))

        # Build lipid type lookup
        lipid_types = {lt.id: lt for lt in config.lipid_types}

        # Create parametric curve
        curve = self._create_curve(config)

        # Place lipids
        placer = LipidPlacer(curve, config.membrane, config.composition, lipid_types)
        lipid_instances = placer.place_all()

        # Apply raft mode (modify instances in raft zones)
        if config.raft_mode.enabled:
            lipid_instances = self._apply_raft(config, lipid_instances, lipid_types)

        # Filter pore exclusion zones and compute pore lipids
        pore_instances: list[LipidInstance] = []
        if config.pore_mode.enabled:
            arc_len = max(curve.arc_length(), 1)
            first_type = next(iter(config.composition.outer_leaflet.ratios.keys()), "PC")
            for pl in config.pore_mode.placements:
                pore_t = pl.position_t
                pore_half = config.pore_mode.pore_radius / arc_len * 2
                lipid_instances = [
                    li for li in lipid_instances
                    if abs(li.t - pore_t) > pore_half
                ]
                cp = curve.sample(pore_t)
                pore_instances_raw = compute_toroidal_pore_lipids(
                    cp.x, cp.y,
                    config.pore_mode.pore_radius,
                    config.membrane.width,
                    config.pore_mode.num_lipids_in_pore,
                )
                for pp in pore_instances_raw:
                    pore_instances.append(LipidInstance(
                        lipid_type_id=first_type,
                        x=pp.x, y=pp.y,
                        angle=pp.angle,
                        scale=1.0,
                        leaflet="pore",
                        t=pore_t,
                    ))

        # ── Render layers ──

        # 1. Membrane background
        svg.add(render_membrane_background(curve, config.membrane))

        # 2. Pore water fill
        if config.pore_mode.enabled:
            for pl in config.pore_mode.placements:
                cp = curve.sample(pl.position_t)
                svg.add(svg_ellipse(
                    cp.x, cp.y,
                    config.pore_mode.pore_radius,
                    config.membrane.width / 2,
                    fill="#AED6F1", fill_opacity=0.3, stroke="none",
                ))

        # 3. Lipids
        geo_mode = config.membrane.show_geometric_shapes
        show_kinks = config.membrane.show_kinks
        show_head_stroke = config.membrane.show_head_stroke
        half_w = config.membrane.width / 2
        tail_hw = half_w * config.membrane.tail_length_factor

        # 3D depth rows: render back rows of heads-only before the front row
        if config.membrane.show_3d and config.membrane.shape == MembraneShape.LINEAR:
            self._render_3d_depth_rows(svg, config, lipid_instances, lipid_types, curve)

        for inst in lipid_instances + pore_instances:
            lt = lipid_types.get(inst.lipid_type_id)
            if not lt:
                continue
            lipid_svg = render_lipid(lt, config.membrane.lipid_base_size, geo_mode, tail_hw, show_kinks, show_head_stroke)
            angle_deg = math.degrees(inst.angle) - 90
            t = transform_str(inst.x, inst.y, angle_deg, inst.scale)
            svg.add(f'<g transform="{t}">{lipid_svg}</g>')

        # 4. Proteins
        for prot in config.proteins:
            cp = curve.sample(prot.position_t)
            prot_svg = render_protein(prot, config.membrane.width)
            angle_deg = math.degrees(cp.angle) + 90
            t = transform_str(cp.x, cp.y, angle_deg)
            svg.add(f'<g transform="{t}">{prot_svg}</g>')

        # 5. Scissor mode
        if config.scissor_mode.enabled:
            self._render_scissors(svg, config, curve)

        # 6. Annotations
        ann_svg = render_annotations(
            config.annotations, curve, config.membrane,
            config.canvas_width, config.canvas_height,
        )
        if ann_svg:
            svg.add(ann_svg)

        # 7. Legend
        if config.show_legend:
            legend_svg = render_legend(
                lipid_types, config.composition,
                config.canvas_width - 150, 10,
            )
            if legend_svg:
                svg.add(legend_svg)

        return svg.render()

    def _create_curve(self, config: SceneConfig) -> ParametricCurve:
        """Build the parametric curve for the membrane shape."""
        m = config.membrane
        cx = config.canvas_width / 2
        cy = config.canvas_height / 2

        if m.shape == MembraneShape.LINEAR:
            x0 = (config.canvas_width - m.length) / 2
            return LinearCurve(x0, cy, m.length)

        elif m.shape == MembraneShape.CIRCULAR:
            return CircularCurve(cx, cy, m.radius)

        elif m.shape == MembraneShape.ELLIPTICAL:
            return EllipticalCurve(cx, cy, m.ellipse_rx, m.ellipse_ry)

        elif m.shape == MembraneShape.BEZIER:
            knots = [(p[0], p[1]) for p in m.bezier_points if len(p) >= 2]
            if len(knots) < 2:
                return LinearCurve((config.canvas_width - m.length) / 2, cy, m.length)
            handles = m.bezier_handles if m.bezier_handles else None
            return build_spline_curve(knots, handles=handles)

        elif m.shape == MembraneShape.CRISTAE:
            total_w = (
                m.cristae_width * m.cristae_count
                + m.cristae_spacing * max(0, m.cristae_count - 1)
                + 200  # flat extensions
            )
            start_x = (config.canvas_width - total_w) / 2
            return build_cristae_curve(
                base_y=cy - m.cristae_depth / 3,
                start_x=start_x,
                cristae_width=m.cristae_width,
                cristae_depth=m.cristae_depth,
                cristae_count=m.cristae_count,
                cristae_spacing=m.cristae_spacing,
            )

        return LinearCurve((config.canvas_width - m.length) / 2, cy, m.length)

    def _apply_raft(
        self,
        config: SceneConfig,
        instances: list[LipidInstance],
        lipid_types: dict[str, LipidType],
    ) -> list[LipidInstance]:
        """Apply raft mode: thicken lipids in raft regions."""
        raft = config.raft_mode
        result: list[LipidInstance] = []
        for inst in instances:
            for pl in raft.placements:
                if pl.start_t <= inst.t <= pl.end_t:
                    inst.scale *= raft.thickness_factor
                    break
            result.append(inst)
        return result

    def _render_scissors(
        self,
        svg: SVGBuilder,
        config: SceneConfig,
        curve: ParametricCurve,
    ) -> None:
        """Render scissor icons at user-specified positions."""
        sc = config.scissor_mode
        half = config.membrane.width / 2

        for placement in sc.placements:
            cp = curve.sample(placement.position_t)
            # Position the scissor on the specified leaflet
            if placement.leaflet == "outer":
                sx = cp.x + cp.normal_x * (half + 12)
                sy = cp.y + cp.normal_y * (half + 12)
                # Blades toward membrane = opposite to normal
                angle_deg = math.degrees(
                    math.atan2(-cp.normal_y, -cp.normal_x)
                )
            else:
                sx = cp.x - cp.normal_x * (half + 12)
                sy = cp.y - cp.normal_y * (half + 12)
                # Blades toward membrane = along normal
                angle_deg = math.degrees(
                    math.atan2(cp.normal_y, cp.normal_x)
                )
            svg.add(render_scissor_icon(
                sx, sy, angle_deg, sc.scissor_color,
                size=sc.scissor_size, enzyme=sc.enzyme,
            ))

    def _render_3d_depth_rows(
        self,
        svg: SVGBuilder,
        config: SceneConfig,
        lipid_instances: list[LipidInstance],
        lipid_types: dict[str, LipidType],
        curve: ParametricCurve,
    ) -> None:
        """Render isometric 3D depth effect — outer leaflet only.

        Each back layer k (1..depth_rows-1):
          - Has (N - k) circles (drops k lipids from the right end)
          - X positions shifted right by k × half_spacing
          - Y positions shifted up by k × row_spacing
          - Color lightened proportionally to distance from front

        This creates an oblique isometric perspective where back rows are
        progressively narrower, shifted right, and lighter — matching the
        reference 3d.svg.
        """
        m = config.membrane
        depth_rows = m.depth_rows
        row_sp = m.row_spacing
        scale = m.lipid_base_size / 12.0
        show_head_stroke = m.show_head_stroke
        base_head_r = 4.5 * scale

        # Lighten factor per row
        lighten_per_row = 0.77 / max(depth_rows - 1, 1)

        # Sort outer lipids by X to get the ordered front row
        outer_lipids = sorted(
            [li for li in lipid_instances if li.leaflet == "outer"],
            key=lambda li: li.x,
        )
        n = len(outer_lipids)
        if n < 2:
            return

        # Compute the inter-lipid spacing from the front row
        spacing = (outer_lipids[-1].x - outer_lipids[0].x) / (n - 1)
        half_spacing = spacing / 2.0

        # Y shift per row = half_spacing × 0.5 (isometric ~27° angle from reference)
        # row_spacing slider scales this: default 6 → factor 1.0
        y_per_row = half_spacing * 0.5 * (row_sp / 6.0)

        # Render from furthest back (lightest) to just behind front (darkest)
        for k in range(depth_rows - 1, 0, -1):
            lighten_factor = k * lighten_per_row
            # Drop the last k lipids from the sorted list
            row_lipids = outer_lipids[: n - k]

            for inst in row_lipids:
                lt = lipid_types.get(inst.lipid_type_id)
                if not lt:
                    continue

                head_r = base_head_r * lt.head_radius_factor

                # Shift right by half_spacing × k, up from head position by y_per_row × k
                hx = inst.x + half_spacing * k
                hy = inst.y - base_head_r - y_per_row * k

                head_color = _lighten_color(lt.head_color, lighten_factor)

                if show_head_stroke:
                    stroke_color = _lighten_color("#333333", lighten_factor)
                    stroke_w = 0.6
                else:
                    stroke_color = "none"
                    stroke_w = 0

                svg.add(svg_circle(
                    hx, hy, head_r,
                    fill=head_color,
                    stroke=stroke_color,
                    stroke_width=stroke_w,
                ))
