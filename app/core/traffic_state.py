"""
Live traffic state store.

Holds the authoritative in-process snapshot of per-edge traffic metrics.
The SimulationManager writes here every tick; routing and API layers read it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from app.utils.constants import CongestionLevel


@dataclass
class EdgeState:
    edge_id: str
    speed: float = 0.0
    vehicle_count: int = 0
    congestion_score: float = 0.0
    congestion_level: CongestionLevel = CongestionLevel.FREE_FLOW


class TrafficStateStore:
    """Thread-local-safe, in-process cache of the latest edge-level traffic state."""

    def __init__(self) -> None:
        self._states: Dict[str, EdgeState] = {}

    def update(
        self,
        edge_id: str,
        speed: float,
        vehicle_count: int,
        congestion_score: float,
        congestion_level: CongestionLevel,
    ) -> None:
        self._states[edge_id] = EdgeState(
            edge_id=edge_id,
            speed=speed,
            vehicle_count=vehicle_count,
            congestion_score=congestion_score,
            congestion_level=congestion_level,
        )

    def get(self, edge_id: str) -> Optional[EdgeState]:
        return self._states.get(edge_id)

    def all_states(self) -> Dict[str, EdgeState]:
        return dict(self._states)

    def clear(self) -> None:
        self._states.clear()


# Module-level singleton.
traffic_state_store = TrafficStateStore()
