"""
haversine_utils.py
==================
Reusable Haversine great-circle distance calculation for the
Disaster Response Dashboard spatial-temporal detection layer.

Formula
-------
d = 2R * asin(sqrt(sin²((lat2-lat1)/2) + cos(lat1)*cos(lat2)*sin²((lon2-lon1)/2)))

where R = 6371 km (mean Earth radius).

Returns distance in kilometres.

Usage
-----
    from backend.services.haversine_utils import calculate_haversine_distance

    dist_km = calculate_haversine_distance(28.6700, 77.2700, 28.6701, 77.2701)

Design notes
------------
- Pure function, fully deterministic.
- Coordinates must be in decimal degrees.
- Returns 0.0 for identical coordinates (no division-by-zero risk).
- Does not raise on valid floating-point inputs; callers must guard against
  None / NaN values before calling.
"""

from __future__ import annotations

import math
from typing import Optional

# Mean Earth radius in kilometres (WGS-84 approximation used by this project).
EARTH_RADIUS_KM: float = 6371.0

#: Spatial proximity threshold (kilometres, Haversine great-circle distance)
#: shared by the conflict detector and duplicate detector engines.
SPATIAL_THRESHOLD_KM: float = 1.0


def calculate_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Return the great-circle distance in kilometres between two points.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of point 1 in decimal degrees.
    lat2, lon2 : float
        Latitude and longitude of point 2 in decimal degrees.

    Returns
    -------
    float
        Distance in kilometres (≥ 0.0).

    Examples
    --------
    >>> calculate_haversine_distance(0.0, 0.0, 0.0, 0.0)   # same point
    0.0
    >>> round(calculate_haversine_distance(28.670, 77.270, 28.671, 77.271), 3)
    0.148
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2
    )
    # clamp 'a' to [0, 1] to guard against floating-point rounding producing
    # values infinitesimally outside the domain of sqrt / asin.
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def safe_haversine_distance(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
) -> Optional[float]:
    """Return Haversine distance or None if any coordinate is missing/None.

    This wrapper is used by the detection engines to safely handle reports
    that are missing latitude or longitude values without raising exceptions.

    Returns
    -------
    float or None
        Distance in km, or None if any input coordinate is None.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    return calculate_haversine_distance(lat1, lon1, lat2, lon2)
