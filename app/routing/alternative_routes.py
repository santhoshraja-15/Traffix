"""
Alternative-routes generator.

Uses ``all_simple_paths`` to enumerate candidate paths and returns the top N
ranked by total weight. Thin layer on top of ``shortest_path.py`` kept
separate so it can evolve (e.g. penalise path overlap) without touching the
main routing pipeline.
"""
from __future__ import annotations

from typing import List

import networkx as nx

from app.routing.shortest_path import all_simple_paths, path_weight
from app.utils.logging import get_logger

logger = get_logger(__name__)


def get_alternative_routes(
    graph: nx.DiGraph,
    source: str,
    target: str,
    count: int = 3,
    cutoff: int = 14,
) -> List[List[str]]:
    """
    Return up to *count* alternative node paths from *source* to *target*,
    ordered by ascending total edge weight.
    """
    candidates = all_simple_paths(graph, source, target, cutoff=cutoff)
    if not candidates:
        logger.debug("No alternative paths found: %s → %s", source, target)
        return []

    ranked = sorted(candidates, key=lambda p: path_weight(graph, p))
    result = ranked[:count]
    logger.debug(
        "Found %d alternative(s) for %s → %s (requested %d)",
        len(result),
        source,
        target,
        count,
    )
    return result
