"""
Pathfinding over the live, congestion-weighted road graph.

calculate_top_routes() returns up to `count` distinct simple paths from
source to destination, ranked by total (congestion-adjusted) travel time,
using nx.shortest_simple_paths (a Yen's-algorithm-style k-shortest-paths
generator) so alternatives are genuinely different routes rather than
near-duplicates of the best path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import networkx as nx

from app.utils.logging import get_logger

logger = get_logger(__name__)


class NodeNotFoundError(ValueError):
    """Raised when a requested source/destination node isn't in the graph."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' not found in the road network graph")


class NoRouteFoundError(ValueError):
    """Raised when source and destination exist but no path connects them."""

    def __init__(self, source: str, dest: str) -> None:
        self.source = source
        self.dest = dest
        super().__init__(f"No route found between '{source}' and '{dest}'")


@dataclass
class PathResult:
    rank: int
    node_path: List[str]
    edge_ids: List[str] = field(default_factory=list)
    total_travel_time: float = 0.0
    total_distance_m: float = 0.0
    avg_congestion: float = 0.0


def calculate_top_routes(
    graph: nx.DiGraph,
    source: str,
    dest: str,
    count: int = 3,
) -> List[PathResult]:
    """
    Return up to `count` ranked PathResult objects from source to dest,
    using live edge "weight" (congestion-adjusted travel time) as cost.

    Raises NodeNotFoundError if source or dest isn't in the graph, and
    NoRouteFoundError if both exist but are disconnected.
    """
    if source not in graph:
        raise NodeNotFoundError(source)
    if dest not in graph:
        raise NodeNotFoundError(dest)

    if source == dest:
        return [
            PathResult(
                rank=0,
                node_path=[source],
                edge_ids=[],
                total_travel_time=0.0,
                total_distance_m=0.0,
                avg_congestion=0.0,
            )
        ]

    try:
        path_generator = nx.shortest_simple_paths(graph, source, dest, weight="weight")
    except nx.NetworkXNoPath as exc:
        raise NoRouteFoundError(source, dest) from exc
    except nx.NodeNotFound as exc:
        # Defensive: shouldn't hit this since we checked membership above.
        raise NodeNotFoundError(str(exc)) from exc

    results: List[PathResult] = []
    for rank, node_path in enumerate(path_generator):
        if rank >= count:
            break
        edge_ids: List[str] = []
        total_time = 0.0
        total_distance = 0.0
        total_congestion = 0.0

        for u, v in zip(node_path[:-1], node_path[1:]):
            edge_data = graph[u][v]
            edge_ids.append(edge_data.get("edge_id", f"{u}->{v}"))
            total_time += edge_data.get("weight", 0.0)
            total_distance += edge_data.get("length_m", 0.0)
            total_congestion += edge_data.get("congestion", 0.0)

        num_edges = max(1, len(edge_ids))
        results.append(
            PathResult(
                rank=rank,
                node_path=node_path,
                edge_ids=edge_ids,
                total_travel_time=total_time,
                total_distance_m=total_distance,
                avg_congestion=total_congestion / num_edges,
            )
        )

    if not results:
        raise NoRouteFoundError(source, dest)

    return results
