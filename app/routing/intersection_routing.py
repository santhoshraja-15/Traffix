"""
Intersection-aware routing helpers.

Adds turn-penalty and signal-phase costs at intersections so routes prefer
paths with fewer stop-light delays. Wraps the base graph with augmented
turn weights for pathfinding.
"""
from __future__ import annotations

from typing import Dict, Optional

import networkx as nx

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Default additional delay (seconds) for each turn type.
DEFAULT_TURN_PENALTIES: Dict[str, float] = {
    "left_turn": 15.0,
    "right_turn": 5.0,
    "u_turn": 30.0,
    "straight": 0.0,
    "signal_red": 45.0,
}


def apply_intersection_penalties(
    graph: nx.DiGraph,
    penalties: Optional[Dict[str, float]] = None,
) -> None:
    """
    Mutate edge weights in-place to incorporate intersection turn penalties.

    In the mock grid all intersections are treated as signalised with a flat
    signal delay added to the first edge of each path segment (edges that
    *originate* from a node with degree > 2, i.e. a real intersection).

    In production, replace this with OSM turn-restriction data.
    """
    p = penalties or DEFAULT_TURN_PENALTIES
    signal_delay = p.get("signal_red", 45.0)
    updated = 0

    for node in graph.nodes():
        in_degree = graph.in_degree(node)   # type: ignore[arg-type]
        out_degree = graph.out_degree(node)  # type: ignore[arg-type]
        is_intersection = in_degree > 1 and out_degree > 1

        if is_intersection:
            # Add signal delay to every outgoing edge from this intersection.
            for _, v, data in graph.out_edges(node, data=True):
                base = data.get("base_weight", data.get("weight", 1.0))
                data["weight"] = base + signal_delay
                updated += 1

    logger.debug("Applied intersection penalties to %d outgoing edges.", updated)
