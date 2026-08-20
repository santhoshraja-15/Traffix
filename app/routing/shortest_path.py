"""
Dijkstra / k-shortest-paths wrappers.

Thin wrappers around networkx shortest-path algorithms. Separated here so
``dynamic_routing.py`` can call them and the routing layer stays testable
in isolation.
"""
from __future__ import annotations

from typing import List, Optional

import networkx as nx

from app.utils.logging import get_logger

logger = get_logger(__name__)


def dijkstra_path(
    graph: nx.DiGraph,
    source: str,
    target: str,
    weight: str = "weight",
) -> Optional[List[str]]:
    """
    Return the shortest node path from *source* to *target* using Dijkstra.
    Returns ``None`` if no path exists.
    """
    try:
        return nx.shortest_path(graph, source, target, weight=weight)  # type: ignore[return-value]
    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        logger.debug("No shortest path %s → %s: %s", source, target, exc)
        return None


def all_simple_paths(
    graph: nx.DiGraph,
    source: str,
    target: str,
    cutoff: int = 12,
) -> List[List[str]]:
    """
    Enumerate simple paths up to *cutoff* hops.  Useful for alternative-route
    generation but can be expensive on large graphs; keep cutoff small.
    """
    try:
        return list(nx.all_simple_paths(graph, source, target, cutoff=cutoff))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def path_weight(graph: nx.DiGraph, node_path: List[str], weight: str = "weight") -> float:
    """Sum edge weights along *node_path*."""
    total = 0.0
    for u, v in zip(node_path, node_path[1:]):
        edge_data = graph.get_edge_data(u, v) or {}
        total += float(edge_data.get(weight, 1.0))
    return total
