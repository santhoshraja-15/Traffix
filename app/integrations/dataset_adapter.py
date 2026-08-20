"""
Dataset adapter.

Loads historical traffic datasets (CSV/Parquet) and exposes them as
Pandas DataFrames for model training and offline analytics.
For the hackathon, returns synthetic data when the file is not present.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent / "ml" / "artifacts" / "traffic_data.csv"


class DatasetAdapter:
    """Loads tabular traffic data for model training / feature analysis."""

    def __init__(self, dataset_path: Optional[Path] = None) -> None:
        self._path = dataset_path or DEFAULT_DATASET_PATH

    def load(self):  # -> pd.DataFrame (avoid hard dep at import time)
        """Return traffic DataFrame; synthesises data if file is absent."""
        try:
            import pandas as pd

            if self._path.exists():
                df = pd.read_csv(self._path)
                logger.info("Loaded dataset from %s (%d rows).", self._path, len(df))
                return df

            logger.warning("Dataset not found at %s — generating synthetic data.", self._path)
            return self._synthetic()
        except ImportError:
            logger.error("pandas is not installed — cannot load dataset.")
            return None

    @staticmethod
    def _synthetic():
        import pandas as pd
        import numpy as np

        rng = np.random.default_rng(42)
        n = 500
        return pd.DataFrame(
            {
                "edge_id": [f"n{rng.integers(0,5)}_{rng.integers(0,5)}->n{rng.integers(0,5)}_{rng.integers(0,5)}" for _ in range(n)],
                "vehicle_count": rng.integers(0, 120, n),
                "avg_speed": rng.uniform(5, 60, n).round(1),
                "capacity": [120] * n,
                "hour_of_day": rng.integers(0, 24, n),
                "rainfall": rng.uniform(0, 1, n).round(2),
                "congested": rng.integers(0, 2, n),
            }
        )
