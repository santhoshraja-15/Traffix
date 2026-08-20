"""
Ambulance dispatcher.

Selects the nearest available ambulance to a reported accident and
initiates dispatch via AmbulanceManager, then triggers green-corridor
setup via GreenCorridor.
"""
from __future__ import annotations

from typing import Optional

from app.emergency.ambulance_manager import AmbulanceRecord, ambulance_manager
from app.routing.graph_manager import get_road_network_graph
from app.routing.shortest_path import dijkstra_path
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _nearest_available(accident_node: str) -> Optional[AmbulanceRecord]:
    """
    Return the closest available ambulance to *accident_node* by hop count.
    Falls back to any available unit if pathfinding fails.
    """
    graph = get_road_network_graph().graph
    units = ambulance_manager.available_units()
    if not units:
        return None

    best: Optional[AmbulanceRecord] = None
    best_hops = float("inf")

    for unit in units:
        path = dijkstra_path(graph, unit.current_node, accident_node)
        hops = len(path) - 1 if path else float("inf")
        if hops < best_hops:
            best_hops = hops
            best = unit

    return best


def dispatch_ambulance(accident_id: str, accident_node: str) -> Optional[str]:
    """
    Select and dispatch the nearest available ambulance to *accident_node*.

    Returns the ambulance_id of the dispatched unit, or ``None`` if none
    is available.
    """
    unit = _nearest_available(accident_node)
    if unit is None:
        logger.warning("dispatch_ambulance: no available units for accident %s.", accident_id)
        return None

    success = ambulance_manager.dispatch(unit.ambulance_id, accident_id)
    if success:
        logger.info(
            "Dispatched %s (node=%s) to accident %s (node=%s).",
            unit.unit_number,
            unit.current_node,
            accident_id,
            accident_node,
        )
        return unit.ambulance_id

    return None
