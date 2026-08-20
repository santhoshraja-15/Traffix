"""
Congestion prediction interface.

Thin wrapper that wires feature_builder → model → output dict.
Callers import ``predict`` and never touch the model directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.ml.feature_builder import build_feature_matrix
from app.utils.logging import get_logger

logger = get_logger(__name__)


def predict(
    edge_rows: List[Dict[str, Any]],
    model: Optional[Any] = None,
) -> Dict[str, float]:
    """
    Predict congestion probability (0.0-1.0) for each edge in *edge_rows*.

    If *model* is ``None`` a simple heuristic is used instead (same as the
    fallback in ``existing_ml_adapter``), keeping the interface usable before
    a trained model artifact exists.

    Returns:
        Dict mapping ``edge_id`` → congestion probability.
    """
    if not edge_rows:
        return {}

    if model is not None:
        try:
            features = build_feature_matrix(edge_rows)
            raw = model.predict_proba(features)
            scores = [float(p[1]) if len(p) > 1 else float(p[0]) for p in raw]
        except Exception as exc:  # noqa: BLE001
            logger.error("predictor: model inference failed, using heuristic: %s", exc)
            scores = [_heuristic(r) for r in edge_rows]
    else:
        scores = [_heuristic(r) for r in edge_rows]

    return {
        str(row.get("edge_id", idx)): max(0.0, min(1.0, score))
        for idx, (row, score) in enumerate(zip(edge_rows, scores))
    }


def _heuristic(row: Dict[str, Any]) -> float:
    vc = float(row.get("vehicle_count", 0) or 0)
    cap = float(row.get("capacity", 100) or 100) or 1.0
    spd = float(row.get("avg_speed", 40) or 40)
    rain = float(row.get("rainfall", 0) or 0)
    occ = min(vc / cap, 1.5)
    spd_f = max(0.0, 1.0 - spd / 60.0)
    return max(0.0, min(1.0, 0.6 * occ + 0.3 * spd_f + 0.2 * rain))
