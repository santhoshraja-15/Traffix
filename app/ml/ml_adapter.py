"""
TRAFFICX V15 - ML Adapter
=========================

This module is the **single source of truth** for the V15 XGBoost model contract.

``V15_FEATURES`` is the hardcoded, ordered list of feature columns that the
model was trained on.  Every piece of live data **must** be mapped to this
exact list before calling ``predict()``.  Column order is law — XGBoost reads
arrays, not column names.

``TrafficModelAdapter`` is the FastAPI-friendly wrapper.  The server calls
``TrafficModelAdapter()`` once during startup and stores it in
``app.state.ml_engine``.  At prediction time, callers pass a plain dict of
road metrics and get back a ``float`` risk probability in [0, 1].
"""
from __future__ import annotations

import os
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import xgboost as xgb

from app.utils.logging import get_logger

logger = get_logger(__name__)


# ============================================================
# V15 FEATURE CONTRACT
# ============================================================
# THIS IS THE LAW.
# The model was trained on these 53 columns, in exactly this order.
# If you change the order, or add/remove a column, predictions will
# be random noise.  Do NOT re-order without re-training.
# ============================================================

V15_FEATURES: List[str] = [
    # ── Base features (19) ──────────────────────────────────────────
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",
    "road_length_m",
    "vehicles_per_100m",
    "queue_ratio",
    "previous_speed_kmh",
    "previous_vehicle_count",
    "previous_density",
    "previous_queue_length_m",
    "speed_change_kmh",
    "vehicle_change",
    "density_change",
    "queue_change_m",
    "speed_change_pct",
    "vehicle_change_pct",

    # ── Lag-2 state (5) ─────────────────────────────────────────────
    "speed_lag2",
    "vehicle_lag2",
    "density_lag2",
    "queue_lag2",
    "stopped_lag2",

    # ── Lag-3 state (5) ─────────────────────────────────────────────
    "speed_lag3",
    "vehicle_lag3",
    "density_lag3",
    "queue_lag3",
    "stopped_lag3",

    # ── 2-step momentum (5) ─────────────────────────────────────────
    "speed_change_2step",
    "vehicle_change_2step",
    "density_change_2step",
    "queue_change_2step",
    "stopped_change_2step",

    # ── 3-step momentum (5) ─────────────────────────────────────────
    "speed_change_3step",
    "vehicle_change_3step",
    "density_change_3step",
    "queue_change_3step",
    "stopped_change_3step",

    # ── Risk escalation rates (5) ───────────────────────────────────
    "speed_reduction_rate",
    "density_growth_rate",
    "queue_growth_rate",
    "vehicle_growth_rate",
    "stopped_growth_rate",

    # ── Second-order / acceleration (5) ─────────────────────────────
    "speed_acceleration",
    "density_acceleration",
    "queue_acceleration",
    "vehicle_acceleration",
    "stopped_acceleration",

    # ── Interaction / composite (4) ─────────────────────────────────
    "traffic_pressure",
    "queue_density_pressure",
    "speed_density_ratio",
    "escalation_score",
]

# Total: 53 features — must match model's booster.num_features()
V15_FEATURE_COUNT: int = len(V15_FEATURES)


# ============================================================
# MODEL PATH
# ============================================================

_WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"

# Canonical name from train_xgboost_v15.py. Also accept download copies
# such as "trafficx_xgboost_v15_risk_escalation (1).json".
_DEFAULT_MODEL_PATH = _WEIGHTS_DIR / "trafficx_xgboost_v15_risk_escalation.json"


def resolve_v15_model_path() -> Path:
    env = os.environ.get("TRAFFICX_V15_MODEL_PATH")
    if env:
        return Path(env)
    if _DEFAULT_MODEL_PATH.exists():
        return _DEFAULT_MODEL_PATH
    matches = sorted(_WEIGHTS_DIR.glob("trafficx_xgboost_v15_risk_escalation*.json"))
    if matches:
        return matches[0]
    return _DEFAULT_MODEL_PATH

# Classification threshold chosen during V15 threshold optimisation pass.
# Requires precision >= 0.60 and maximises F1.  Override via env var.
V15_THRESHOLD: float = float(os.environ.get("TRAFFICX_V15_THRESHOLD", "0.96"))


# ============================================================
# TRAFFIC MODEL ADAPTER
# ============================================================

class TrafficModelAdapter:
    """
    FastAPI-friendly wrapper around the V15 XGBoost risk model.

    Lifecycle
    ---------
    Instantiate once during server startup (inside the ``lifespan`` context
    manager) and store on ``app.state.ml_engine``.  The constructor loads the
    model from disk into RAM so that all subsequent prediction calls are
    purely in-memory.

    Usage
    -----
    ::

        adapter = TrafficModelAdapter()
        risk_prob = adapter.predict(road_feature_dict)
        is_risky  = risk_prob >= adapter.threshold
    """

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        threshold: float = V15_THRESHOLD,
    ) -> None:
        self.threshold = threshold
        self._model: Optional[xgb.XGBClassifier] = None

        path = Path(model_path) if model_path else resolve_v15_model_path()
        self._load_model(path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_model(self, path: Path) -> None:
        """Load V15 XGBoost model from *path* into RAM."""
        if not path.exists():
            logger.warning(
                "TrafficModelAdapter: model file not found at %s. "
                "Predictions will return 0.0 until the model is present.",
                path,
            )
            return

        try:
            model = xgb.XGBClassifier()
            model.load_model(str(path))

            # Verify feature count matches our contract
            try:
                booster_n = model.get_booster().num_features()
                if booster_n != V15_FEATURE_COUNT:
                    logger.error(
                        "TrafficModelAdapter: feature count mismatch! "
                        "Model expects %d features but V15_FEATURES defines %d. "
                        "Re-train or update V15_FEATURES.",
                        booster_n,
                        V15_FEATURE_COUNT,
                    )
            except Exception:
                pass  # Non-fatal — older XGBoost may not expose num_features

            self._model = model
            logger.info(
                "TrafficModelAdapter: V15 model loaded from %s "
                "(%d features, threshold=%.2f).",
                path,
                V15_FEATURE_COUNT,
                self.threshold,
            )

        except Exception as exc:
            logger.error(
                "TrafficModelAdapter: failed to load model from %s: %s",
                path,
                exc,
            )

    # ------------------------------------------------------------------
    # Feature engineering helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_div(a: float, b: float) -> float:
        """Division that returns 0.0 on zero-denominator or NaN."""
        return float(a) / float(b) if b and not math.isnan(b) else 0.0

    @classmethod
    def build_features(cls, raw: Dict[str, Any]) -> pd.DataFrame:
        """
        Build a single-row DataFrame that matches V15_FEATURES exactly.

        Parameters
        ----------
        raw:
            Dict containing road telemetry.  All V15 temporal/lag/escalation
            features are expected to be pre-computed by the caller (e.g. the
            road collector).  Any missing key defaults to 0.0.

        Returns
        -------
        pd.DataFrame
            Shape (1, 53) with columns in the *exact* V15 contract order.
            Ready to pass to ``model.predict_proba()``.
        """
        row = {col: float(raw.get(col, 0.0)) for col in V15_FEATURES}
        df = pd.DataFrame([row], columns=V15_FEATURES)
        # Replace inf / NaN with 0 — mirrors training-time fillna(0.0)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return df

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """Return True if the underlying model is loaded and ready."""
        return self._model is not None

    def predict(self, raw: Dict[str, Any]) -> float:
        """
        Predict risk probability for a single road segment snapshot.

        Parameters
        ----------
        raw:
            Flat dict of road metrics.  Keys must match those in V15_FEATURES;
            missing keys default to 0.0.

        Returns
        -------
        float
            Risk probability in [0, 1].  Returns 0.0 if model is not loaded.
        """
        if self._model is None:
            logger.debug("TrafficModelAdapter.predict: model not loaded, returning 0.0")
            return 0.0

        X = self.build_features(raw)

        try:
            prob: float = float(self._model.predict_proba(X)[0, 1])
            return prob
        except Exception as exc:
            logger.error("TrafficModelAdapter.predict error: %s", exc)
            return 0.0

    def predict_batch(self, rows: List[Dict[str, Any]]) -> List[float]:
        """
        Predict risk probabilities for a batch of road snapshots.

        Parameters
        ----------
        rows:
            List of raw road metric dicts.

        Returns
        -------
        List[float]
            Probabilities in [0, 1], one per input row.
        """
        if self._model is None:
            return [0.0] * len(rows)

        if not rows:
            return []

        frames = [self.build_features(r) for r in rows]
        X = pd.concat(frames, ignore_index=True)

        try:
            probs = self._model.predict_proba(X)[:, 1].tolist()
            return probs
        except Exception as exc:
            logger.error("TrafficModelAdapter.predict_batch error: %s", exc)
            return [0.0] * len(rows)

    def is_high_risk(self, raw: Dict[str, Any]) -> bool:
        """Convenience wrapper — True if risk probability >= threshold."""
        return self.predict(raw) >= self.threshold

    def __repr__(self) -> str:
        status = "LOADED" if self.is_ready else "NOT LOADED"
        return (
            f"<TrafficModelAdapter V15 [{status}] "
            f"features={V15_FEATURE_COUNT} threshold={self.threshold}>"
        )

