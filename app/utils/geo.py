"""Geo helper functions (WGS84 lat/lng, matching the frontend coordinate system).

Public surface:
  haversine_distance_m   – canonical name, uses lng parameter labels.
  haversine_distance     – alias with lon parameter labels (matches task spec & frontend convention).
  bearing_deg            – initial compass bearing between two points.
  interpolate            – linear lat/lng interpolation along a short segment.
"""
from __future__ import annotations

import math

from app.utils.constants import EARTH_RADIUS_METERS


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in meters between two WGS84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_METERS * c


def bearing_deg(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial compass bearing in degrees from point 1 to point 2 (0-360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lng2 - lng1)

    x = math.sin(d_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def interpolate(lat1: float, lng1: float, lat2: float, lng2: float, fraction: float) -> tuple[float, float]:
    """Linear lat/lng interpolation, fraction in [0, 1]. Good enough for short edges at city scale."""
    fraction = max(0.0, min(1.0, fraction))
    return (
        lat1 + (lat2 - lat1) * fraction,
        lng1 + (lng2 - lng1) * fraction,
    )


# ---------------------------------------------------------------------------
# Convenience alias: lon parameter labels match the frontend JS convention.
# ---------------------------------------------------------------------------

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance in meters between two WGS84 points.

    Alias for ``haversine_distance_m`` using ``lon`` parameter names so callers
    following the frontend JS convention (lon vs lng) don't need to rename their
    variables.  Satisfies the task-spec signature:
        haversine_distance(lat1, lon1, lat2, lon2) -> float
    """
    return haversine_distance_m(lat1, lon1, lat2, lon2)
