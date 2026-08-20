"""
Application configuration.

Kept as a plain class (not pydantic-settings, to avoid an extra dependency
beyond the hackathon requirements.txt). Reads simple overrides from
environment variables where useful.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


def _env_list(name: str, default: List[str]) -> List[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "TRAFFICX API"
    app_version: str = "0.1.0"
    debug: bool = os.getenv("TRAFFICX_DEBUG", "true").lower() == "true"

    host: str = os.getenv("TRAFFICX_HOST", "0.0.0.0")
    port: int = int(os.getenv("TRAFFICX_PORT", "8000"))

    cors_allow_origins: List[str] = field(
        default_factory=lambda: _env_list("TRAFFICX_CORS_ORIGINS", ["*"])
    )

    # Simulation defaults
    default_simulation_tick_seconds: float = 1.0
    default_vehicle_density: float = 0.5

    # Routing defaults
    default_route_alternatives: int = 3


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor -- import and call this, don't instantiate Settings() directly."""
    return Settings()
