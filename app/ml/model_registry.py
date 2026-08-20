"""
Model registry.

Central catalogue of all ML model artifacts used by the application.
Provides a unified interface to load, reload, or query available models
without scattering path logic across modules.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"

_KNOWN_MODELS: Dict[str, str] = {
    "congestion": "congestion_model.joblib",
}


class ModelRegistry:
    """Loads and caches joblib model artifacts by logical name."""

    def __init__(self, artifact_dir: Path = ARTIFACT_DIR) -> None:
        self._dir = artifact_dir
        self._cache: Dict[str, Any] = {}

    def load(self, name: str, force_reload: bool = False) -> Optional[Any]:
        """
        Load model *name* from the artifact directory.

        Returns the model object, or ``None`` if the artifact is missing.
        Results are cached; pass ``force_reload=True`` to bypass the cache.
        """
        if name in self._cache and not force_reload:
            return self._cache[name]

        filename = _KNOWN_MODELS.get(name)
        if not filename:
            logger.warning("ModelRegistry: unknown model name '%s'.", name)
            return None

        path = self._dir / filename
        if not path.exists():
            logger.warning("ModelRegistry: artifact not found at %s.", path)
            return None

        try:
            import joblib
            model = joblib.load(path)
            self._cache[name] = model
            logger.info("ModelRegistry: loaded '%s' from %s.", name, path)
            return model
        except Exception as exc:  # noqa: BLE001
            logger.error("ModelRegistry: failed to load '%s': %s", name, exc)
            return None

    def is_available(self, name: str) -> bool:
        filename = _KNOWN_MODELS.get(name)
        if not filename:
            return False
        return (self._dir / filename).exists()

    def available_models(self) -> Dict[str, bool]:
        return {name: self.is_available(name) for name in _KNOWN_MODELS}


# Module-level singleton.
model_registry = ModelRegistry()
