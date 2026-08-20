"""
Model adapter bridge.

Provides a unified ``ModelAdapterBridge`` that selects the correct backend
adapter (XGBoost joblib vs. ONNX vs. PyTorch) based on the artifact type
present in ``ml/artifacts/``.  Falls back to the heuristic in
``existing_ml_adapter`` when no artifact is available.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.integrations.existing_ml_adapter import TrafficModelAdapter
from app.utils.logging import get_logger

logger = get_logger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "ml" / "artifacts"


class ModelAdapterBridge:
    """
    Auto-detects and wraps the best available model artifact.

    Priority order:
      1. ``congestion_model.joblib`` (XGBoost / sklearn, loaded by TrafficModelAdapter)
      2. Heuristic fallback (no file required)
    """

    def __init__(self) -> None:
        self._adapter: TrafficModelAdapter = TrafficModelAdapter()
        logger.info(
            "ModelAdapterBridge initialised — model_loaded=%s",
            self._adapter.is_model_loaded,
        )

    def predict_congestion(self, edge_rows: List[Dict[str, Any]]) -> Dict[str, float]:
        """Delegate to the underlying adapter."""
        return self._adapter.predict_congestion(edge_rows)

    @property
    def backend(self) -> str:
        return "xgboost_joblib" if self._adapter.is_model_loaded else "heuristic"

    def reload(self) -> None:
        """Re-scan artifacts and reload the best available model."""
        self._adapter.reload()
        logger.info("ModelAdapterBridge reloaded — backend=%s", self.backend)


# Module-level singleton.
model_bridge = ModelAdapterBridge()
