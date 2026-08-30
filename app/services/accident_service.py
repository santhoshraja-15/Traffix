"""
Accident service.

Bridges the API layer with AccidentManager and the routing graph, so
accident endpoints never import emergency/routing internals directly.

report_accident() also automatically starts a real emergency mission
(app.emergency.mission_manager) — nearest real hospital, real ambulance,
real route — matching MASTER_PROMPT.md's "whenever an active accident is
detected, automatically run a full simulated emergency response." This
deliberately does NOT go through the older
app.emergency.emergency_routing.handle_accident() (which still assumes
the old synthetic mock-grid's node IDs and has no state-machine/tick-
driven timing at all) — mission_manager.py is the real, tick-driven
replacement for that path.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.emergency.accident_manager import AccidentRecord, accident_manager
from app.routing.graph_manager import get_road_network_graph
from app.utils.logging import get_logger

logger = get_logger(__name__)

# How much an accident reduces the affected edge's effective capacity, by
# severity — feeds directly into the existing occupancy-driven congestion/
# risk heuristics (vehicle_count / capacity), so this is a real, measurable
# network impact through the same pipeline that already scores every other
# edge, not a separate invented effect. Accepts both the frontend's 4-level
# scale (low/medium/high/critical) and the shorter aliases already used
# elsewhere in this module (minor/moderate).
_SEVERITY_CAPACITY_FACTOR: Dict[str, float] = {
    "low": 0.75,
    "minor": 0.75,
    "medium": 0.55,
    "moderate": 0.55,
    "high": 0.35,
    "critical": 0.15,
}
_DEFAULT_CAPACITY_FACTOR = 0.5


class AccidentService:
    """High-level accident operations for the API layer."""

    def __init__(self) -> None:
        # accident_id -> the edge's capacity before this accident reduced it,
        # so resolve_accident() can restore it exactly.
        self._original_capacity_by_accident: Dict[str, float] = {}

    def report_accident(
        self,
        edge_id: str,
        severity: str = "moderate",
        location_description: str = "",
    ) -> dict:
        """
        Record a new accident on *edge_id* and apply a real capacity
        reduction to that edge so it genuinely shows up as higher
        congestion/risk on the next simulation tick — not a cosmetic flag.

        Returns a response dict suitable for direct serialisation.
        """
        record = accident_manager.report(edge_id, severity, location_description)

        graph = get_road_network_graph()
        factor = _SEVERITY_CAPACITY_FACTOR.get(severity.lower(), _DEFAULT_CAPACITY_FACTOR)
        original_capacity = graph.apply_capacity_multiplier(edge_id, factor)
        if original_capacity is not None:
            self._original_capacity_by_accident[record.accident_id] = original_capacity
            logger.info(
                "AccidentService: capacity on edge %s reduced x%.2f (accident %s, severity=%s)",
                edge_id, factor, record.accident_id, severity,
            )
        else:
            logger.warning(
                "AccidentService: edge %s not found in the current graph — "
                "accident %s recorded but no capacity impact applied.",
                edge_id, record.accident_id,
            )

        # Automatically dispatch a real emergency mission — nearest real
        # hospital + ambulance + real route. Declines honestly (logs why,
        # doesn't fabricate) if no hospital/ambulance/route is available;
        # the accident itself is still recorded and has its real impact
        # either way.
        from app.emergency.mission_manager import mission_manager  # noqa: PLC0415
        from app.core.simulation_manager import simulation_manager  # noqa: PLC0415

        ids = simulation_manager.active_simulations
        current_tick = simulation_manager.tick_count(ids[0]) if ids else 0
        mission = mission_manager.start_mission(record.accident_id, edge_id, current_tick)

        location = graph.get_edge_midpoint(edge_id)
        return {
            "accident_id": record.accident_id,
            "edge_id": edge_id,
            "severity": severity,
            "location_description": location_description,
            "location": {"lat": location[0], "lng": location[1]} if location else None,
            "road_name": graph.get_edge_name(edge_id),
            "status": "active",
            "mission_dispatched": mission is not None,
        }

    def resolve_accident(self, accident_id: str) -> bool:
        """Mark *accident_id* resolved and restore the edge's real capacity."""
        record = accident_manager.get(accident_id)
        if record is None:
            return False

        original_capacity = self._original_capacity_by_accident.pop(accident_id, None)
        if original_capacity is not None:
            get_road_network_graph().restore_capacity(record.edge_id, original_capacity)
            logger.info(
                "AccidentService: capacity on edge %s restored (accident %s resolved)",
                record.edge_id, accident_id,
            )

        return accident_manager.resolve(accident_id)

    def active_accidents(self) -> List[AccidentRecord]:
        return accident_manager.active_accidents()

    def get_accident(self, accident_id: str) -> Optional[AccidentRecord]:
        return accident_manager.get(accident_id)


# Module-level singleton.
_default_accident_service: Optional[AccidentService] = None


def get_accident_service() -> AccidentService:
    global _default_accident_service
    if _default_accident_service is None:
        _default_accident_service = AccidentService()
    return _default_accident_service
