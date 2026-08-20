"""
Risk scoring engine.

Computes a composite road-segment risk score combining congestion probability,
accident history, and environmental factors (rainfall, time-of-day).
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.utils.logging import get_logger

logger = get_logger(__name__)


def compute_risk_score(
    congestion_probability: float,
    rainfall: float = 0.0,
    hour_of_day: int = 12,
    accident_flag: bool = False,
) -> float:
    """
    Return a risk score in [0, 1] for a road segment.

    Combines:
      - congestion probability  (weight: 0.5)
      - rainfall intensity       (weight: 0.2)
      - night-time factor        (weight: 0.15)  — hours 22-05 are riskier
      - active accident          (flat: +0.20)
    """
    night_hours = set(range(22, 24)) | set(range(0, 6))
    night_factor = 1.0 if hour_of_day in night_hours else 0.0

    score = (
        0.50 * congestion_probability
        + 0.20 * min(rainfall, 1.0)
        + 0.15 * night_factor
        + (0.20 if accident_flag else 0.0)
    )
    return max(0.0, min(1.0, score))


def score_edge_risks(
    edge_rows: List[Dict[str, Any]],
    congestion_scores: Dict[str, float],
) -> Dict[str, float]:
    """
    Batch-compute risk scores for a list of edge feature rows.

    Args:
        edge_rows: List of dicts with keys ``edge_id``, ``rainfall``,
                   ``hour_of_day``, ``accident_flag``.
        congestion_scores: Mapping of edge_id → congestion probability.

    Returns:
        Mapping of edge_id → risk score.
    """
    results: Dict[str, float] = {}
    for row in edge_rows:
        eid = str(row.get("edge_id", ""))
        cong = congestion_scores.get(eid, 0.0)
        results[eid] = compute_risk_score(
            congestion_probability=cong,
            rainfall=float(row.get("rainfall", 0.0) or 0.0),
            hour_of_day=int(row.get("hour_of_day", 12) or 12),
            accident_flag=bool(row.get("accident_flag", False)),
        )
    return results
