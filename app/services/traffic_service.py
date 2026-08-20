"""
Traffic service.

Provides point-in-time and aggregate traffic state queries for the
traffic API and analytics layers.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.core.traffic_state import EdgeState, traffic_state_store
from app.routing.graph_manager import get_road_network_graph
from app.utils.constants import CongestionLevel
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TrafficService:
    """Queries and aggregates live traffic state data."""

    def get_edge_state(self, edge_id: str) -> Optional[EdgeState]:
        """Return the latest cached state for *edge_id*, or ``None``."""
        return traffic_state_store.get(edge_id)

    def get_all_states(self) -> Dict[str, EdgeState]:
        """Return all cached edge states."""
        return traffic_state_store.all_states()

    def get_congestion_summary(self) -> Dict[str, int]:
        """
        Count edges in each CongestionLevel category.

        Returns a dict mapping level name → count.
        """
        summary: Dict[str, int] = {level.value: 0 for level in CongestionLevel}
        for state in traffic_state_store.all_states().values():
            summary[state.congestion_level.value] = summary.get(state.congestion_level.value, 0) + 1
        return summary

    def get_network_avg_speed(self) -> float:
        """Return the mean speed across all edges with a cached state."""
        states = list(traffic_state_store.all_states().values())
        if not states:
            return 0.0
        return round(sum(s.speed for s in states) / len(states), 2)


# Module-level singleton.
_default_traffic_service: Optional[TrafficService] = None


def get_traffic_service() -> TrafficService:
    global _default_traffic_service
    if _default_traffic_service is None:
        _default_traffic_service = TrafficService()
    return _default_traffic_service
