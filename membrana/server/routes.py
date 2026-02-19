"""REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from ..models.lipids import DEFAULT_LIPID_TYPES
from ..models.scene import SceneConfig
from ..presets.registry import PresetRegistry
from ..rendering.scene_renderer import SceneRenderer

router = APIRouter()
_renderer = SceneRenderer()
_presets = PresetRegistry()


@router.post("/render")
async def render_svg(config: SceneConfig):
    """Render SVG from configuration."""
    svg_str = _renderer.render(config)
    return {"svg": svg_str}


@router.get("/presets")
async def list_presets():
    """List available presets."""
    return {"presets": _presets.list_summaries()}


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    config = _presets.get(preset_id)
    if config is None:
        return {"error": f"Preset '{preset_id}' not found"}
    return config.model_dump()


@router.get("/lipid-types")
async def list_lipid_types():
    """Return default lipid type library."""
    return {"lipid_types": [lt.model_dump() for lt in DEFAULT_LIPID_TYPES]}


@router.post("/export")
async def export_svg(config: SceneConfig):
    """Export SVG as downloadable file."""
    svg_str = _renderer.render(config)
    return Response(
        content=svg_str,
        media_type="image/svg+xml",
        headers={"Content-Disposition": 'attachment; filename="membrane.svg"'},
    )


@router.post("/sample-curve")
async def sample_curve(config: SceneConfig, num_points: int = 20):
    """Sample the current parametric curve at N evenly-spaced points.

    Used by the frontend to convert any shape to a Bezier spline.
    For closed shapes (circle, ellipse), the first point is repeated at the
    end so the Catmull-Rom spline closes the loop.
    """
    num_points = max(3, min(num_points, 100))
    curve = _renderer._create_curve(config)
    points: list[list[float]] = []
    if curve.is_closed:
        # Sample N points around the closed shape, then repeat first to close
        for i in range(num_points):
            t = i / num_points  # don't reach t=1.0 (same as t=0)
            x, y = curve.point(t)
            points.append([round(x, 1), round(y, 1)])
        points.append(list(points[0]))  # close the loop
    else:
        for i in range(num_points):
            t = i / (num_points - 1)
            x, y = curve.point(t)
            points.append([round(x, 1), round(y, 1)])
    return {"points": points}
