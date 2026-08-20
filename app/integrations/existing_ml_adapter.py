"""
Adapter over the XGBoost congestion model.

Loads a trained model from app/ml/artifacts/ if present. If the artifact is
missing (e.g. not trained yet during the hackathon), predict_congestion()
falls back to a deterministic heuristic score so the rest of the pipeline
keeps working end-to-end.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "ml" / "artifacts"
DEFAULT_MODEL_FILENAME = "congestion_model.joblib"

# Feature keys expected in each edge_data dict passed to predict_congestion.
# Missing keys are defaulted, so callers can pass partial data.
_EXPECTED_FEATURES = ["vehicle_count", "avg_speed", "capacity", "hour_of_day", "rainfall"]


class TrafficModelAdapter:
    """Wraps a trained XGBoost congestion model with a safe fallback path."""

    def __init__(self, artifact_path: Optional[Path] = None) -> None:
        self._artifact_path = artifact_path or (ARTIFACT_DIR / DEFAULT_MODEL_FILENAME)
        self._model: Optional[Any] = None
        self._loaded = False
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load the model file. Never raises -- logs and falls back instead."""
        if not self._artifact_path.exists():
            logger.warning(
                "ML artifact not found at %s -- predict_congestion() will use the "
                "heuristic fallback until a model is trained/placed there.",
                self._artifact_path,
            )
            self._model = None
            self._loaded = False
            return

        try:
            import joblib

            self._model = joblib.load(self._artifact_path)
            self._loaded = True
            logger.info("Loaded XGBoost congestion model from %s", self._artifact_path)
        except Exception as exc:  # noqa: BLE001 - any load failure should degrade, not crash
            logger.error("Failed to load ML artifact at %s: %s", self._artifact_path, exc)
            self._model = None
            self._loaded = False

    @property
    def is_model_loaded(self) -> bool:
        return self._loaded and self._model is not None

    def reload(self) -> None:
        """Re-attempt loading the artifact (e.g. after a fresh training run drops it in)."""
        self._load_model()

    def _vectorize(self, edge_data: List[Dict[str, Any]]) -> List[List[float]]:
        rows: List[List[float]] = []
        for row in edge_data:
            rows.append([float(row.get(key, 0.0) or 0.0) for key in _EXPECTED_FEATURES])
        return rows

    def _fallback_score(self, row: Dict[str, Any]) -> float:
        """
        Deterministic heuristic used when no trained model is available:
        higher vehicle count relative to capacity, lower speed, and rainfall
        all push the congestion probability up. Clamped to [0, 1].
        """
        vehicle_count = float(row.get("vehicle_count", 0.0) or 0.0)
        capacity = float(row.get("capacity", 100.0) or 100.0) or 1.0
        avg_speed = float(row.get("avg_speed", 40.0) or 40.0)
        rainfall = float(row.get("rainfall", 0.0) or 0.0)

        occupancy_ratio = min(vehicle_count / capacity, 1.5)
        speed_factor = max(0.0, 1.0 - (avg_speed / 60.0))
        rain_factor = min(rainfall, 1.0) * 0.2

        score = 0.6 * occupancy_ratio + 0.3 * speed_factor + rain_factor
        return max(0.0, min(1.0, score))

    def predict_congestion(self, edge_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Predict congestion probability (0.0-1.0) per edge.

        edge_data: list of dicts, each containing at least "edge_id" plus any
        of the feature keys in _EXPECTED_FEATURES. Unknown/missing features
        default to 0.
        """
        if not edge_data:
            return {}

        if self.is_model_loaded:
            try:
                features = self._vectorize(edge_data)
                raw_predictions = self._model.predict_proba(features)  # type: ignore[union-attr]
                # Assume binary classifier: probability of the "congested" class (index 1)
                scores = [float(p[1]) if len(p) > 1 else float(p[0]) for p in raw_predictions]
            except Exception as exc:  # noqa: BLE001 - model errors shouldn't break routing
                logger.error("Model inference failed, falling back to heuristic: %s", exc)
                scores = [self._fallback_score(row) for row in edge_data]
        else:
            scores = [self._fallback_score(row) for row in edge_data]

        return {
            str(row.get("edge_id", idx)): max(0.0, min(1.0, score))
            for idx, (row, score) in enumerate(zip(edge_data, scores))
        }


# Module-level singleton for convenient reuse across services without re-loading the model.
_default_adapter: Optional[TrafficModelAdapter] = None


def get_model_adapter() -> TrafficModelAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = TrafficModelAdapter()
    return _default_adapter
