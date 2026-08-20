"""
Green corridor management.

A "green corridor" temporarily boosts signal priority on the edges of an
emergency route so an ambulance can traverse them without stopping.
In the mock implementation we lower edge weights on the path to simulate
signal pre-emption.
"""
from __future__ import annotations

from typing import List, Optional

import networkx as nx

from app.routing.graph_manager import get_road_network_graph
from app.routing.shortest_path import dijkstra_path
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Fraction of original weight kept during a green-corridor activation.
# 0.1 = 90 % time reduction → ambulance is nearly unimpeded.
GREEN_CORRIDOR_WEIGHT_FACTOR = 0.1


class GreenCorridor:
    """
    Manages temporary weight overrides on the routing graph to create a
    signal-prioritised corridor for an emergency vehicle.
    """

    def __init__(self) -> None:
        # Maps ambulance_id → list of (u, v, original_weight) tuples for cleanup.
        self._active: dict[str, list[tuple[str, str, float]]] = {}

    def activate(
        self,
        ambulance_id: str,
        origin_node: str,
        destination_node: str,
    ) -> Optional[List[str]]:
        """
        Compute the shortest path and lower edge weights along it.

        Returns the node path used for the corridor, or ``None`` if no path
        exists.
        """
        graph = get_road_network_graph().graph
        path = dijkstra_path(graph, origin_node, destination_node)
        if not path:
            logger.warning(
                "GreenCorridor: no path %s → %s for ambulance %s.",
                origin_node,
                destination_node,
                ambulance_id,
            )
            return None

        overrides: list[tuple[str, str, float]] = []
        for u, v in zip(path, path[1:]):
            data = graph.get_edge_data(u, v)
            if data:
                original = float(data.get("weight", 1.0))
                data["weight"] = original * GREEN_CORRIDOR_WEIGHT_FACTOR
                overrides.append((u, v, original))

        self._active[ambulance_id] = overrides
        logger.info(
            "Green corridor activated for ambulance %s: %d edges prioritised.",
            ambulance_id,
            len(overrides),
        )
        return path

    def deactivate(self, ambulance_id: str) -> None:
        """Restore original edge weights when the ambulance has passed."""
        overrides = self._active.pop(ambulance_id, [])
        if not overrides:
            return
        graph = get_road_network_graph().graph
        for u, v, original in overrides:
            if graph.has_edge(u, v):
                graph[u][v]["weight"] = original
        logger.info(
            "Green corridor deactivated for ambulance %s (%d edges restored).",
            ambulance_id,
            len(overrides),
        )


# Module-level singleton.
green_corridor = GreenCorridor()
