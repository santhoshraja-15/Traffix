"""
ML feature engineering for the congestion model.

Transforms raw edge sensor readings into a normalised feature vector that
matches the XGBoost model's expected input schema.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


_FEATURE_KEYS = ["vehicle_count", "avg_speed", "capacity", "hour_of_day", "rainfall"]


def build_feature_vector(edge_data: Dict[str, Any]) -> List[float]:
    """
    Convert a single edge-data dict into a flat float feature vector.

    Missing keys default to zero. The order must match the column order the
    model was trained on (see ``_FEATURE_KEYS``).
    """
    hour = datetime.now(timezone.utc).hour
    return [
        float(edge_data.get("vehicle_count", 0) or 0),
        float(edge_data.get("avg_speed", 0) or 0),
        float(edge_data.get("capacity", 120) or 120),
        float(edge_data.get("hour_of_day", hour) or hour),
        float(edge_data.get("rainfall", 0) or 0),
    ]


def build_feature_matrix(edge_rows: List[Dict[str, Any]]) -> List[List[float]]:
    """Build a feature matrix (list of feature vectors) from multiple edge rows."""
    return [build_feature_vector(row) for row in edge_rows]


def feature_names() -> List[str]:
    """Return the ordered feature names matching ``build_feature_vector``."""
    return list(_FEATURE_KEYS)
