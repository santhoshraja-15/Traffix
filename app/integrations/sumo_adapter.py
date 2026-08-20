"""
SUMO simulation adapter stub.

In production, this module starts / controls a SUMO simulation process
via the subprocess API and exposes a clean Python interface.
For the hackathon, it stubs the interface so the rest of the app can import
and call it without a SUMO installation present.
"""
from __future__ import annotations

from app.utils.logging import get_logger

logger = get_logger(__name__)


class SumoAdapter:
    """
    Stub SUMO simulation adapter.

    Replace the method bodies with real ``subprocess`` / socket calls once
    SUMO is available in the deployment environment.
    """

    def __init__(self, config_path: str = "sumo.cfg") -> None:
        self._config_path = config_path
        self._running = False

    def start(self) -> bool:
        logger.info("[STUB] SumoAdapter.start() — SUMO not installed, returning mock ok.")
        self._running = True
        return True

    def stop(self) -> None:
        logger.info("[STUB] SumoAdapter.stop()")
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def get_vehicle_positions(self) -> dict:
        """Return a mock vehicle position dict keyed by vehicle_id."""
        return {"veh_0": {"edge": "n0_0->n0_1", "x": 13.0827, "y": 80.2707, "speed": 35.0}}

    def inject_scenario(self, scenario_type: str, **kwargs) -> bool:
        logger.info("[STUB] SumoAdapter.inject_scenario: %s %s", scenario_type, kwargs)
        return True
