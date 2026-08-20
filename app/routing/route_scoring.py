"""
Route scoring utilities.

Computes a composite score for each candidate route so the routing layer
can rank them consistently. The score is a weighted combination of:
  - Normalised travel time (primary)
  - Average congestion level (secondary)
  - Distance penalty (minor)

Lower score = better route.
"""
from __future__ import annotations

from typing import List


def compute_route_score(
    travel_time: float,
    avg_congestion: float,
    distance_m: float,
    *,
    time_weight: float = 0.6,
    congestion_weight: float = 0.3,
    distance_weight: float = 0.1,
    max_time: float = 3600.0,
    max_distance: float = 50_000.0,
) -> float:
    """
    Return a composite score in [0, 1] — lower is better.

    All three inputs are normalised to [0, 1] before weighting so the
    scale of each metric doesn't dominate the others.
    """
    norm_time = min(travel_time / max_time, 1.0)
    norm_congestion = min(avg_congestion, 1.0)
    norm_distance = min(distance_m / max_distance, 1.0)

    return (
        time_weight * norm_time
        + congestion_weight * norm_congestion
        + distance_weight * norm_distance
    )


def rank_routes(
    routes: List[dict],
    time_weight: float = 0.6,
    congestion_weight: float = 0.3,
    distance_weight: float = 0.1,
) -> List[dict]:
    """
    Attach a ``_score`` field to each route dict and return them sorted
    ascending (best first).

    Expected keys in each dict: ``travel_time``, ``avg_congestion``, ``distance_m``.
    """
    for route in routes:
        route["_score"] = compute_route_score(
            travel_time=route.get("travel_time", 0.0),
            avg_congestion=route.get("avg_congestion", 0.0),
            distance_m=route.get("distance_m", 0.0),
            time_weight=time_weight,
            congestion_weight=congestion_weight,
            distance_weight=distance_weight,
        )
    return sorted(routes, key=lambda r: r["_score"])
