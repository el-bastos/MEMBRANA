"""Parametric curve definitions for membrane shapes."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import NamedTuple


class CurvePoint(NamedTuple):
    x: float
    y: float
    normal_x: float
    normal_y: float
    angle: float  # Angle of normal in radians


class ParametricCurve(ABC):
    """Abstract base class for membrane centerline curves."""

    @abstractmethod
    def point(self, t: float) -> tuple[float, float]:
        """Return (x, y) at parameter t in [0, 1]."""

    @abstractmethod
    def tangent(self, t: float) -> tuple[float, float]:
        """Return tangent vector at t (not necessarily normalized)."""

    def normal(self, t: float) -> tuple[float, float]:
        """Unit normal perpendicular to tangent, pointing outward."""
        tx, ty = self.tangent(t)
        length = math.hypot(tx, ty)
        if length < 1e-10:
            return (0.0, -1.0)
        # Rotate tangent -90 degrees (outward = upward for left-to-right curves)
        return (-ty / length, tx / length)

    def sample(self, t: float) -> CurvePoint:
        x, y = self.point(t)
        nx, ny = self.normal(t)
        angle = math.atan2(ny, nx)
        return CurvePoint(x, y, nx, ny, angle)

    @abstractmethod
    def arc_length(self) -> float:
        """Total arc length."""

    def sample_uniform(self, spacing: float) -> list[CurvePoint]:
        """Sample at uniform arc-length intervals."""
        total = self.arc_length()
        n = max(1, int(total / spacing))

        # Build cumulative arc length table (adaptive sampling)
        num_samples = max(500, n * 10)
        table: list[tuple[float, float]] = []  # (t, cumulative_length)
        cum = 0.0
        prev_x, prev_y = self.point(0.0)
        table.append((0.0, 0.0))

        for i in range(1, num_samples + 1):
            t = i / num_samples
            px, py = self.point(t)
            cum += math.hypot(px - prev_x, py - prev_y)
            table.append((t, cum))
            prev_x, prev_y = px, py

        total_measured = table[-1][1]
        if total_measured < 1e-10:
            return [self.sample(0.5)]

        actual_spacing = total_measured / n
        points: list[CurvePoint] = []
        table_idx = 0

        for i in range(n):
            target_s = (i + 0.5) * actual_spacing
            # Binary search in table
            while table_idx < len(table) - 1 and table[table_idx + 1][1] < target_s:
                table_idx += 1

            if table_idx >= len(table) - 1:
                t = 1.0
            else:
                t0, s0 = table[table_idx]
                t1, s1 = table[min(table_idx + 1, len(table) - 1)]
                ds = s1 - s0
                if ds < 1e-10:
                    t = t0
                else:
                    frac = (target_s - s0) / ds
                    t = t0 + frac * (t1 - t0)

            points.append(self.sample(t))

        return points

    @property
    def is_closed(self) -> bool:
        return False


class LinearCurve(ParametricCurve):
    """Straight horizontal line. Normal points upward (outer leaflet on top)."""

    def __init__(self, x0: float, y0: float, length: float):
        self.x0 = x0
        self.y0 = y0
        self.length = length

    def point(self, t: float) -> tuple[float, float]:
        return (self.x0 + t * self.length, self.y0)

    def tangent(self, t: float) -> tuple[float, float]:
        return (1.0, 0.0)

    def normal(self, t: float) -> tuple[float, float]:
        return (0.0, -1.0)  # Upward in SVG (outer leaflet faces up)

    def arc_length(self) -> float:
        return self.length


class CircularCurve(ParametricCurve):
    """Circle (closed vesicle)."""

    def __init__(self, cx: float, cy: float, radius: float):
        self.cx = cx
        self.cy = cy
        self.radius = radius

    def point(self, t: float) -> tuple[float, float]:
        angle = 2 * math.pi * t
        return (
            self.cx + self.radius * math.cos(angle),
            self.cy + self.radius * math.sin(angle),
        )

    def tangent(self, t: float) -> tuple[float, float]:
        angle = 2 * math.pi * t
        return (-math.sin(angle), math.cos(angle))

    def normal(self, t: float) -> tuple[float, float]:
        """For a circle, normal points radially outward."""
        angle = 2 * math.pi * t
        return (math.cos(angle), math.sin(angle))

    def arc_length(self) -> float:
        return 2 * math.pi * self.radius

    @property
    def is_closed(self) -> bool:
        return True


class EllipticalCurve(ParametricCurve):
    """Ellipse (closed vesicle)."""

    def __init__(self, cx: float, cy: float, rx: float, ry: float):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry

    def point(self, t: float) -> tuple[float, float]:
        angle = 2 * math.pi * t
        return (
            self.cx + self.rx * math.cos(angle),
            self.cy + self.ry * math.sin(angle),
        )

    def tangent(self, t: float) -> tuple[float, float]:
        angle = 2 * math.pi * t
        return (-self.rx * math.sin(angle), self.ry * math.cos(angle))

    def arc_length(self) -> float:
        # Ramanujan approximation
        h = ((self.rx - self.ry) / (self.rx + self.ry)) ** 2
        return math.pi * (self.rx + self.ry) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))

    @property
    def is_closed(self) -> bool:
        return True


class CompositeCurve(ParametricCurve):
    """Chain of sub-curves joined end-to-end.

    Each sub-curve's t range is proportional to its arc length.
    """

    def __init__(self, curves: list[ParametricCurve], flip_normals: bool = False):
        self.curves = curves
        self._flip_normals = flip_normals
        self._lengths = [c.arc_length() for c in curves]
        self._total = sum(self._lengths)
        # Build cumulative boundaries
        self._boundaries: list[float] = []
        cum = 0.0
        for length in self._lengths:
            cum += length
            self._boundaries.append(cum / self._total if self._total > 0 else 0)

    def _resolve(self, t: float) -> tuple[ParametricCurve, float]:
        """Map global t to (sub-curve, local_t)."""
        t = max(0.0, min(1.0, t))
        prev = 0.0
        for i, boundary in enumerate(self._boundaries):
            if t <= boundary or i == len(self._boundaries) - 1:
                span = boundary - prev
                if span < 1e-10:
                    local_t = 0.0
                else:
                    local_t = (t - prev) / span
                return self.curves[i], local_t
            prev = boundary
        return self.curves[-1], 1.0

    def point(self, t: float) -> tuple[float, float]:
        curve, local_t = self._resolve(t)
        return curve.point(local_t)

    def tangent(self, t: float) -> tuple[float, float]:
        curve, local_t = self._resolve(t)
        return curve.tangent(local_t)

    def normal(self, t: float) -> tuple[float, float]:
        curve, local_t = self._resolve(t)
        nx, ny = curve.normal(local_t)
        if self._flip_normals:
            return (-nx, -ny)
        return (nx, ny)

    def arc_length(self) -> float:
        return self._total


class LineSegmentCurve(ParametricCurve):
    """Straight line from (x0, y0) to (x1, y1)."""

    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self.x0, self.y0 = x0, y0
        self.x1, self.y1 = x1, y1
        self._dx = x1 - x0
        self._dy = y1 - y0

    def point(self, t: float) -> tuple[float, float]:
        return (self.x0 + t * self._dx, self.y0 + t * self._dy)

    def tangent(self, t: float) -> tuple[float, float]:
        return (self._dx, self._dy)

    def arc_length(self) -> float:
        return math.hypot(self._dx, self._dy)


class ArcCurve(ParametricCurve):
    """Circular arc from start_angle to end_angle (radians)."""

    def __init__(
        self,
        cx: float, cy: float,
        radius: float,
        start_angle: float,
        end_angle: float,
    ):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle

    def point(self, t: float) -> tuple[float, float]:
        angle = self.start_angle + t * (self.end_angle - self.start_angle)
        return (
            self.cx + self.radius * math.cos(angle),
            self.cy + self.radius * math.sin(angle),
        )

    def tangent(self, t: float) -> tuple[float, float]:
        angle = self.start_angle + t * (self.end_angle - self.start_angle)
        direction = 1.0 if self.end_angle > self.start_angle else -1.0
        return (-math.sin(angle) * direction, math.cos(angle) * direction)

    def arc_length(self) -> float:
        return abs(self.end_angle - self.start_angle) * self.radius


class CubicBezierSegment(ParametricCurve):
    """Single cubic Bézier segment defined by 4 control points."""

    def __init__(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
    ):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self._arc_len: float | None = None

    def point(self, t: float) -> tuple[float, float]:
        u = 1.0 - t
        u2 = u * u
        t2 = t * t
        a = u2 * u
        b = 3.0 * u2 * t
        c = 3.0 * u * t2
        d = t2 * t
        return (
            a * self.p0[0] + b * self.p1[0] + c * self.p2[0] + d * self.p3[0],
            a * self.p0[1] + b * self.p1[1] + c * self.p2[1] + d * self.p3[1],
        )

    def tangent(self, t: float) -> tuple[float, float]:
        u = 1.0 - t
        # Derivative: 3[(1-t)²(P1-P0) + 2(1-t)t(P2-P1) + t²(P3-P2)]
        a = 3.0 * u * u
        b = 6.0 * u * t
        c = 3.0 * t * t
        return (
            a * (self.p1[0] - self.p0[0]) + b * (self.p2[0] - self.p1[0]) + c * (self.p3[0] - self.p2[0]),
            a * (self.p1[1] - self.p0[1]) + b * (self.p2[1] - self.p1[1]) + c * (self.p3[1] - self.p2[1]),
        )

    def arc_length(self) -> float:
        if self._arc_len is not None:
            return self._arc_len
        # Numerical integration via polyline approximation
        n = 200
        total = 0.0
        px, py = self.p0
        for i in range(1, n + 1):
            t = i / n
            x, y = self.point(t)
            total += math.hypot(x - px, y - py)
            px, py = x, y
        self._arc_len = total
        return total


def build_spline_curve(
    knots: list[tuple[float, float]],
    handles: list[list[list[float] | None]] | None = None,
) -> CompositeCurve:
    """Build a smooth spline through the given knots using Catmull-Rom → cubic Bézier conversion.

    If handles are provided, they override the auto-computed Catmull-Rom control points.
    handles[i] = [handle_in, handle_out] where each is [dx, dy] offset from knot or None.
    For segment i→i+1: cp1 uses handle_out of knot i, cp2 uses handle_in of knot i+1.

    Returns a CompositeCurve of CubicBezierSegment pieces.
    """
    n = len(knots)
    if n < 2:
        raise ValueError("Need at least 2 knots")
    if n == 2:
        # Just a straight line
        return CompositeCurve([
            LineSegmentCurve(knots[0][0], knots[0][1], knots[1][0], knots[1][1])
        ])

    segments: list[ParametricCurve] = []
    for i in range(n - 1):
        p_i = knots[i]
        p_ip1 = knots[i + 1]

        # Catmull-Rom neighbors (mirror at endpoints)
        if i == 0:
            p_im1 = (2 * p_i[0] - p_ip1[0], 2 * p_i[1] - p_ip1[1])
        else:
            p_im1 = knots[i - 1]

        if i + 2 >= n:
            p_ip2 = (2 * p_ip1[0] - p_i[0], 2 * p_ip1[1] - p_i[1])
        else:
            p_ip2 = knots[i + 2]

        # Catmull-Rom → Bézier control points (tau = 1 for standard CR)
        cp1 = (
            p_i[0] + (p_ip1[0] - p_im1[0]) / 6.0,
            p_i[1] + (p_ip1[1] - p_im1[1]) / 6.0,
        )
        cp2 = (
            p_ip1[0] - (p_ip2[0] - p_i[0]) / 6.0,
            p_ip1[1] - (p_ip2[1] - p_i[1]) / 6.0,
        )

        # Override with explicit handles when provided
        if handles and i < len(handles) and handles[i] and len(handles[i]) > 1:
            out_h = handles[i][1]
            if out_h is not None:
                cp1 = (p_i[0] + out_h[0], p_i[1] + out_h[1])

        if handles and (i + 1) < len(handles) and handles[i + 1]:
            in_h = handles[i + 1][0]
            if in_h is not None:
                cp2 = (p_ip1[0] + in_h[0], p_ip1[1] + in_h[1])

        segments.append(CubicBezierSegment(p_i, cp1, cp2, p_ip1))

    return CompositeCurve(segments)


def build_cristae_curve(
    base_y: float,
    start_x: float,
    cristae_width: float,
    cristae_depth: float,
    cristae_count: int,
    cristae_spacing: float,
    flat_extension: float = 100.0,
) -> CompositeCurve:
    """Build a composite curve for cristae membrane.

    Layout per crista:
        flat -- arc(top-left) -- descent -- U-bend -- ascent -- arc(top-right) -- flat

    Normals are flipped so the outer leaflet faces the IMS/intracristae space.
    Top corners are rounded with small arcs for smooth lipid orientation.
    """
    curves: list[ParametricCurve] = []
    x = start_x
    bend_radius = cristae_width / 2.0
    corner_r = min(40.0, cristae_width * 0.35, cristae_depth * 0.15)

    # Leading flat segment (shortened by corner_r so it connects to first arc)
    if flat_extension > 0:
        lead_end = x + flat_extension - corner_r
        if lead_end > x:
            curves.append(LineSegmentCurve(x, base_y, lead_end, base_y))
        x += flat_extension

    for i in range(cristae_count):
        left_x = x
        right_x = x + cristae_width

        # Top-left corner: smooth RIGHT → DOWN
        # Arc center at (left_x - r, base_y + r)
        # Goes from angle -π/2 (tangent=RIGHT) to 0 (tangent=DOWN)
        curves.append(ArcCurve(
            left_x - corner_r, base_y + corner_r, corner_r,
            -math.pi / 2, 0.0,
        ))

        # Descent (left wall going down, shortened by corner_r at top)
        curves.append(LineSegmentCurve(
            left_x, base_y + corner_r,
            left_x, base_y + cristae_depth,
        ))

        # U-bend at bottom (semicircle from left to right)
        center_x = (left_x + right_x) / 2.0
        bend_y = base_y + cristae_depth
        curves.append(ArcCurve(
            center_x, bend_y, bend_radius,
            math.pi, 0.0,
        ))

        # Ascent (right wall going up, shortened by corner_r at top)
        curves.append(LineSegmentCurve(
            right_x, base_y + cristae_depth,
            right_x, base_y + corner_r,
        ))

        # Top-right corner: smooth UP → RIGHT
        # Arc center at (right_x + r, base_y + r)
        # Goes from angle π (tangent=UP) to 3π/2 (tangent=RIGHT)
        curves.append(ArcCurve(
            right_x + corner_r, base_y + corner_r, corner_r,
            math.pi, 3 * math.pi / 2,
        ))

        x = right_x

        # Spacing between cristae (flat segment, shortened by corner radii)
        if i < cristae_count - 1:
            gap_start = x + corner_r
            gap_end = x + cristae_spacing - corner_r
            if gap_end > gap_start:
                curves.append(LineSegmentCurve(gap_start, base_y, gap_end, base_y))
            x += cristae_spacing

    # Trailing flat segment
    if flat_extension > 0:
        trail_start = x + corner_r
        curves.append(LineSegmentCurve(trail_start, base_y, trail_start + flat_extension, base_y))

    return CompositeCurve(curves, flip_normals=True)
