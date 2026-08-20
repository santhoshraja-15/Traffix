"""
TraCI adapter stub.

TraCI (Traffic Control Interface) is SUMO's remote-control protocol.
This stub exposes the same interface so the routing / emergency layers can
import it without a SUMO/TraCI installation.
"""
from __future__ import annotations

from typing import Dict, List

from app.utils.logging import get_logger

logger = get_logger(__name__)


class TraciAdapter:
    """Stub TraCI adapter — mirrors the real TraCI Python API surface."""

    def __init__(self) -> None:
        self._connected = False

    def connect(self, host: str = "localhost", port: int = 8813) -> bool:
        logger.info("[STUB] TraciAdapter.connect(%s:%d)", host, port)
        self._connected = True
        return True

    def disconnect(self) -> None:
        logger.info("[STUB] TraciAdapter.disconnect()")
        self._connected = False

    def simulation_step(self) -> None:
        if not self._connected:
            logger.warning("[STUB] TraciAdapter.simulation_step called without connection.")

    def get_edge_mean_speed(self, edge_id: str) -> float:
        return 35.0  # mock km/h

    def get_edge_vehicle_count(self, edge_id: str) -> int:
        return 42  # mock count

    def get_all_edge_ids(self) -> List[str]:
        return ["n0_0->n0_1", "n0_1->n0_2", "n1_0->n1_1"]

    def set_traffic_light_phase(self, tl_id: str, phase_index: int) -> None:
        logger.info("[STUB] TraciAdapter: set TL %s → phase %d", tl_id, phase_index)

    def add_vehicle(self, vehicle_id: str, route_id: str, **kwargs) -> None:
        logger.info("[STUB] TraciAdapter: add vehicle %s on route %s", vehicle_id, route_id)
