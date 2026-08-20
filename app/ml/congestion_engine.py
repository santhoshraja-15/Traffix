"""
Congestion prediction engine.

Higher-level engine that combines the feature builder, ML predictor, and
risk engine to produce per-edge congestion labels for routing and
analytics consumers.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.ml.feature_builder import build_feature_matrix
from app.ml.predictor import predict
from app.ml.risk_engine import score_edge_risks
from app.utils.constants import CongestionLevel
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _score_to_level(score: float) -> CongestionLevel:
    if score < 0.2:
        return CongestionLevel.FREE_FLOW
    if score < 0.4:
        return CongestionLevel.LIGHT
    if score < 0.6:
        return CongestionLevel.MODERATE
    if score < 0.8:
        return CongestionLevel.HEAVY
    return CongestionLevel.SEVERE


class CongestionEngine:
    """
    Orchestrates feature building → prediction → risk scoring → label mapping.

    Accepts raw edge-feature rows and returns a rich result dict per edge.
    """

    def __init__(self, model: Any = None) -> None:
        self._model = model  # None → heuristic fallback in predictor

    def analyse(self, edge_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Process *edge_rows* and return a dict mapping edge_id → analysis result.

        Each result dict contains:
          - ``congestion_score``: float [0, 1]
          - ``congestion_level``: CongestionLevel
          - ``risk_score``: float [0, 1]
        """
        congestion_scores = predict(edge_rows, model=self._model)
        risk_scores = score_edge_risks(edge_rows, congestion_scores)

        results: Dict[str, Dict[str, Any]] = {}
        for row in edge_rows:
            eid = str(row.get("edge_id", ""))
            cong = congestion_scores.get(eid, 0.0)
            results[eid] = {
                "congestion_score": round(cong, 4),
                "congestion_level": _score_to_level(cong).value,
                "risk_score": round(risk_scores.get(eid, 0.0), 4),
            }

        logger.debug("CongestionEngine analysed %d edges.", len(results))
        return results


# Module-level singleton — model can be injected after import.
congestion_engine = CongestionEngine()
