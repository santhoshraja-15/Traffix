"""
Route caching layer.

Caches computed candidate-route lists keyed by (source, destination, count)
with a configurable TTL. Prevents redundant graph traversals when the same
route pair is requested multiple times within the TTL window.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

from app.utils.logging import get_logger

logger = get_logger(__name__)

_CacheKey = Tuple[str, str, int]
_CacheEntry = Tuple[float, List[dict]]  # (expire_at, routes)

DEFAULT_TTL_SECONDS: float = 10.0


class RouteCache:
    """Simple TTL-based in-memory route cache."""

    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._store: Dict[_CacheKey, _CacheEntry] = {}

    def get(self, source: str, destination: str, count: int) -> Optional[List[dict]]:
        key: _CacheKey = (source, destination, count)
        entry = self._store.get(key)
        if entry is None:
            return None
        expire_at, routes = entry
        if time.monotonic() > expire_at:
            del self._store[key]
            return None
        logger.debug("Cache hit: %s → %s (count=%d)", source, destination, count)
        return routes

    def set(self, source: str, destination: str, count: int, routes: List[dict]) -> None:
        key: _CacheKey = (source, destination, count)
        self._store[key] = (time.monotonic() + self._ttl, routes)
        logger.debug("Cache set: %s → %s (count=%d, ttl=%.1fs)", source, destination, count, self._ttl)

    def invalidate(self, source: str, destination: str, count: int) -> None:
        self._store.pop((source, destination, count), None)

    def clear(self) -> None:
        self._store.clear()
        logger.debug("Route cache cleared.")


# Module-level singleton.
route_cache = RouteCache()
