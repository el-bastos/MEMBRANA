"""Math utilities for geometry calculations."""

from __future__ import annotations

import math


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smooth Hermite interpolation between 0 and 1."""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def normalize_angle(angle: float) -> float:
    """Normalize angle to [-pi, pi]."""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def vec2_length(x: float, y: float) -> float:
    return math.hypot(x, y)


def vec2_normalize(x: float, y: float) -> tuple[float, float]:
    length = math.hypot(x, y)
    if length < 1e-10:
        return (0.0, 0.0)
    return (x / length, y / length)


def vec2_rotate(x: float, y: float, angle: float) -> tuple[float, float]:
    """Rotate vector by angle (radians)."""
    c = math.cos(angle)
    s = math.sin(angle)
    return (x * c - y * s, x * s + y * c)
