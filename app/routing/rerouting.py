"""
Route rerouting logic.

Computes a new route for an active trip when conditions change mid-journey
(accident detected, congestion surge, etc.). Called by the emergency and
traffic services when a reroute trigger is issued.
"""
from __future__ import annotations

from typing import List, Optional

import networkx as nx

from app.routing.shortest_path import dijkstra_path
from app.utils.logging import get_logger

logger = get_logger(__name__)


def compute_reroute(
    graph: nx.DiGraph,
    current_node: str,
    destination: str,
    avoided_edges: Optional[List[str]] = None,
) -> Optional[List[str]]:
    """
    Return the best reroute from *current_node* to *destination*.

    If *avoided_edges* is provided, those edges are temporarily removed from
    the graph before pathfinding and restored afterwards. This is safe in a
    single-threaded async context because FastAPI/asyncio is single-threaded.

    Returns the node path, or ``None`` if no route can be found.
    """
    avoided_edges = avoided_edges or []
    removed: list[tuple] = []

    # Temporarily remove avoided edges.
    for edge_id in avoided_edges:
        parts = edge_id.split("->") if "->" in edge_id else []
        if len(parts) == 2:
            u, v = parts[0].strip(), parts[1].strip()
            if graph.has_edge(u, v):
                data = graph.get_edge_data(u, v)
                graph.remove_edge(u, v)
                removed.append((u, v, data))

    path = dijkstra_path(graph, current_node, destination)

    # Restore removed edges.
    for u, v, data in removed:
        graph.add_edge(u, v, **(data or {}))

    if path:
        logger.info(
            "Reroute found: %s → %s (%d hops)", current_node, destination, len(path) - 1
        )
    else:
        logger.warning("Reroute failed: no path from %s → %s", current_node, destination)

    return path
