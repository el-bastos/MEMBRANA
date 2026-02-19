"""Lightweight SVG document builder producing clean XML."""

from __future__ import annotations

from typing import Optional


def _fmt(v: float) -> str:
    """Format float for SVG (trim trailing zeros)."""
    s = f"{v:.2f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _attrs(**kwargs: object) -> str:
    parts: list[str] = []
    for k, v in kwargs.items():
        if v is None:
            continue
        svg_key = k.replace("_", "-")
        if isinstance(v, float):
            parts.append(f'{svg_key}="{_fmt(v)}"')
        else:
            parts.append(f'{svg_key}="{v}"')
    return " ".join(parts)


class SVGBuilder:
    """Builds an SVG document from element fragments."""

    def __init__(
        self,
        width: float,
        height: float,
        viewbox: Optional[str] = None,
    ):
        self.width = width
        self.height = height
        self.viewbox = viewbox or f"0 0 {_fmt(width)} {_fmt(height)}"
        self._defs: list[str] = []
        self._elements: list[str] = []

    def add_def(self, svg_fragment: str) -> None:
        self._defs.append(svg_fragment)

    def add(self, svg_fragment: str) -> None:
        self._elements.append(svg_fragment)

    def render(self) -> str:
        defs_block = ""
        if self._defs:
            defs_inner = "\n".join(self._defs)
            defs_block = f"<defs>\n{defs_inner}\n</defs>\n"
        body = "\n".join(self._elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{_fmt(self.width)}" height="{_fmt(self.height)}" '
            f'viewBox="{self.viewbox}">\n'
            f"{defs_block}"
            f"{body}\n"
            f"</svg>"
        )


# ── Element helpers ──────────────────────────────────────────────────────


def svg_circle(cx: float, cy: float, r: float, **kw: object) -> str:
    a = _attrs(cx=cx, cy=cy, r=r, **kw)
    return f"<circle {a}/>"


def svg_rect(x: float, y: float, w: float, h: float, **kw: object) -> str:
    a = _attrs(x=x, y=y, width=w, height=h, **kw)
    return f"<rect {a}/>"


def svg_line(x1: float, y1: float, x2: float, y2: float, **kw: object) -> str:
    a = _attrs(x1=x1, y1=y1, x2=x2, y2=y2, **kw)
    return f"<line {a}/>"


def svg_path(d: str, **kw: object) -> str:
    a = _attrs(d=d, **kw)
    return f"<path {a}/>"


def svg_text(content: str, x: float, y: float, **kw: object) -> str:
    a = _attrs(x=x, y=y, **kw)
    return f"<text {a}>{content}</text>"


def svg_group(children: list[str], **kw: object) -> str:
    a = _attrs(**kw)
    inner = "\n".join(children)
    if a:
        return f"<g {a}>\n{inner}\n</g>"
    return f"<g>\n{inner}\n</g>"


def svg_polygon(points_str: str, **kw: object) -> str:
    a = _attrs(points=points_str, **kw)
    return f"<polygon {a}/>"


def svg_ellipse(cx: float, cy: float, rx: float, ry: float, **kw: object) -> str:
    a = _attrs(cx=cx, cy=cy, rx=rx, ry=ry, **kw)
    return f"<ellipse {a}/>"
