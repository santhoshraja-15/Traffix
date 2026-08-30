"""
Road network graph management.

Wraps a networkx.DiGraph representing the city road network. In the absence
of a real OSM/city dataset (hackathon timeline), initialize_graph() builds a
mock grid so routing has something concrete to operate on immediately; swap
in a real loader later without touching callers.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx

from app.integrations.sumo_network_loader import RealNetwork, get_real_network
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Base free-flow travel time is stored on each edge as "base_weight" and never
# mutated; "weight" is the live, congestion-adjusted value that pathfinding
# actually uses. Keeping both lets us recompute weight from predictions
# without compounding adjustments across repeated calls.
DEFAULT_CONGESTION_MULTIPLIER_RANGE: Tuple[float, float] = (1.0, 4.0)


class RoadNetworkGraph:
    """Owns the live routing graph and its congestion-adjusted edge weights."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._initialized = False
        # "sumo_network" (real Anna Nagar geometry) or "synthetic_fallback"
        # (placeholder grid, used only if the real network fails to load) —
        # exposed via to_geojson() metadata so the frontend can tell honestly
        # apart "this is real" from "this is a degraded placeholder" instead
        # of silently presenting a fake grid as if it were Anna Nagar.
        self._source: str = "uninitialized"

    @property
    def source(self) -> str:
        return self._source

    def initialize_graph(
        self,
        grid_rows: int = 6,
        grid_cols: int = 6,
        base_speed_kmh: float = 40.0,
        edge_length_m: float = 250.0,
    ) -> None:
        """
        Build the routing graph from the real Anna Nagar SUMO network when
        available; fall back to a synthetic placeholder grid only if the
        real network can't be loaded (see
        app.integrations.sumo_network_loader.get_real_network for why that
        might fail — missing dependency, missing file, bad projection).
        """
        real = get_real_network()
        if real is not None:
            self._initialize_from_real_network(real)
            return

        self._initialize_synthetic_grid(grid_rows, grid_cols, base_speed_kmh, edge_length_m)

    def _initialize_from_real_network(self, real: RealNetwork) -> None:
        """Build the graph from real SUMO node/edge geometry — one edge per SUMO edge."""
        self.graph = nx.DiGraph()

        for node in real.nodes:
            self.graph.add_node(node.node_id, lat=node.lat, lng=node.lng)

        # Per-lane capacity heuristic (vehicles the edge can hold at moderate
        # density) — mirrors the mock grid's flat 120 for a single-lane
        # 250 m edge, scaled by real lane count and length.
        per_lane_capacity_per_km = 120.0 / 0.25

        for edge in real.edges:
            if not self.graph.has_node(edge.from_node) or not self.graph.has_node(edge.to_node):
                continue  # defensive — shouldn't happen, every edge endpoint is a parsed node
            speed_kmh = max(edge.speed_limit_kmh, 5.0)
            base_travel_time = edge.length_m / (speed_kmh * 1000 / 3600)  # seconds
            capacity = max(1.0, per_lane_capacity_per_km * (edge.length_m / 1000.0) * edge.lane_count)

            self.graph.add_edge(
                edge.from_node,
                edge.to_node,
                edge_id=edge.edge_id,
                base_weight=base_travel_time,
                weight=base_travel_time,
                congestion=0.0,
                length_m=edge.length_m,
                capacity=capacity,
                lane_count=edge.lane_count,
                speed_limit_kmh=speed_kmh,
                vehicle_count=0,
                avg_speed=speed_kmh,
                # [(lng, lat), ...] — full real geometry, used by to_geojson()
                # instead of a straight line between the two endpoint nodes.
                shape=edge.shape,
            )

        self._initialized = True
        self._source = "sumo_network"
        logger.info(
            "Initialized routing graph from the real Anna Nagar SUMO network: "
            "%d nodes, %d edges.",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    def _initialize_synthetic_grid(
        self,
        grid_rows: int,
        grid_cols: int,
        base_speed_kmh: float,
        edge_length_m: float,
    ) -> None:
        """
        Build a mock rows x cols grid network. Node IDs are "n{row}_{col}";
        edges run bidirectionally between orthogonal neighbors. Each edge
        stores lat/lng (synthetic, small offsets around a fixed origin so the
        frontend map has *something* to render) plus routing attributes.

        This is a degraded fallback only — see initialize_graph(). It does
        not represent real Anna Nagar geometry and self._source reflects
        that so callers/UI can be honest about it.
        """
        self.graph = nx.DiGraph()
        # Anna Nagar, Chennai (Tower / 2nd Avenue grid) — same origin as the
        # real network's approximate center, purely so the placeholder is at
        # least in the right neighborhood if it's ever shown.
        origin_lat, origin_lng = 13.0850, 80.2101
        lat_step, lng_step = 0.0022, 0.0022

        for r in range(grid_rows):
            for c in range(grid_cols):
                node_id = f"n{r}_{c}"
                self.graph.add_node(
                    node_id,
                    lat=origin_lat + r * lat_step,
                    lng=origin_lng + c * lng_step,
                )

        base_travel_time = edge_length_m / (base_speed_kmh * 1000 / 3600)  # seconds

        def add_bidirectional_edge(n1: str, n2: str) -> None:
            for u, v in [(n1, n2), (n2, n1)]:
                edge_id = f"{u}->{v}"
                self.graph.add_edge(
                    u,
                    v,
                    edge_id=edge_id,
                    base_weight=base_travel_time,
                    weight=base_travel_time,
                    congestion=0.0,
                    length_m=edge_length_m,
                    capacity=120,
                    vehicle_count=0,
                    avg_speed=base_speed_kmh,
                )

        for r in range(grid_rows):
            for c in range(grid_cols):
                node_id = f"n{r}_{c}"
                if c + 1 < grid_cols:
                    add_bidirectional_edge(node_id, f"n{r}_{c + 1}")
                if r + 1 < grid_rows:
                    add_bidirectional_edge(node_id, f"n{r + 1}_{c}")

        self._initialized = True
        self._source = "synthetic_fallback"
        logger.warning(
            "Initialized SYNTHETIC PLACEHOLDER grid graph (%d nodes, %d edges) — "
            "the real Anna Nagar network failed to load; see the preceding "
            "error. This graph does NOT represent real geometry.",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    @property
    def is_initialized(self) -> bool:
        return self._initialized and self.graph.number_of_nodes() > 0

    def has_node(self, node_id: str) -> bool:
        return self.graph.has_node(node_id)

    def get_edge_feature_rows(self) -> list[dict]:
        """Export per-edge feature dicts for the ML adapter's predict_congestion()."""
        rows = []
        for u, v, data in self.graph.edges(data=True):
            rows.append(
                {
                    "edge_id": data.get("edge_id", f"{u}->{v}"),
                    "vehicle_count": data.get("vehicle_count", 0),
                    "avg_speed": data.get("avg_speed", 40.0),
                    "capacity": data.get("capacity", 120),
                    "hour_of_day": 12,
                    "rainfall": 0.0,
                }
            )
        return rows

    def update_edge_weights(
        self,
        predictions: Dict[str, float],
        multiplier_range: Tuple[float, float] = DEFAULT_CONGESTION_MULTIPLIER_RANGE,
    ) -> int:
        """
        Adjust each edge's live "weight" from its base_weight using the
        predicted congestion probability (0.0-1.0) for that edge_id.

        weight = base_weight * multiplier, where multiplier scales linearly
        from multiplier_range[0] (no congestion) to multiplier_range[1]
        (fully congested). Edges with no prediction keep their current
        weight unchanged. Returns the count of edges actually updated.
        """
        if not predictions:
            return 0

        low, high = multiplier_range
        updated = 0
        for u, v, data in self.graph.edges(data=True):
            edge_id = data.get("edge_id", f"{u}->{v}")
            score = predictions.get(edge_id)
            if score is None:
                continue
            score = max(0.0, min(1.0, score))
            multiplier = low + (high - low) * score
            base_weight = data.get("base_weight", data.get("weight", 1.0))
            data["weight"] = base_weight * multiplier
            data["congestion"] = score
            updated += 1

        logger.debug("Updated weights on %d/%d edges", updated, self.graph.number_of_edges())
        return updated

    def get_edge_data(self, u: str, v: str) -> Optional[dict]:
        if not self.graph.has_edge(u, v):
            return None
        return dict(self.graph[u][v])

    def get_node_coord(self, node_id: str) -> Optional[Tuple[float, float]]:
        if not self.graph.has_node(node_id):
            return None
        data = self.graph.nodes[node_id]
        return data.get("lat"), data.get("lng")

    def get_nearest_node(self, lat: float, lon: float) -> Tuple[str, float]:
        """
        Return ``(node_id, distance_m)`` for the graph node whose stored
        lat/lng coordinates are closest to *(lat, lon)*.

        Uses the Haversine formula so the result is correct even when the
        grid spans several kilometres.  Nodes missing lat/lng attributes are
        skipped gracefully.

        Raises ``ValueError`` if the graph has no nodes with spatial attributes.
        """
        # Import inside the method to avoid a circular dependency at module
        # load time (geo.py does not import from routing).
        from app.utils.geo import haversine_distance_m  # noqa: PLC0415

        best_id: str = ""
        best_dist: float = float("inf")

        for node_id, data in self.graph.nodes(data=True):
            node_lat = data.get("lat")
            node_lng = data.get("lng")
            if node_lat is None or node_lng is None:
                continue
            dist = haversine_distance_m(lat, lon, node_lat, node_lng)
            if dist < best_dist:
                best_dist = dist
                best_id = str(node_id)

        if not best_id:
            raise ValueError(
                "The graph contains no nodes with lat/lng attributes — "
                "cannot snap coordinates to the nearest node."
            )

        return best_id, best_dist

    def get_graph_bounds(self) -> Optional[Dict[str, float]]:
        """
        Return the bounding box (min/max lat and lng) of all geo-tagged nodes,
        or ``None`` if the graph has no spatial data.  Useful for logging and
        out-of-bounds diagnostics.
        """
        lats: List[float] = []
        lngs: List[float] = []
        for _, data in self.graph.nodes(data=True):
            lat = data.get("lat")
            lng = data.get("lng")
            if lat is not None and lng is not None:
                lats.append(float(lat))
                lngs.append(float(lng))

        if not lats:
            return None

        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs),
        }

    def to_geojson(self, name: str = "Anna Nagar Road Network") -> dict:
        """
        Export the live graph as a GeoJSON FeatureCollection of LineStrings.

        Uses each edge's real, full geometry ("shape") when the graph was
        built from the real SUMO network — never a straight line between the
        two endpoint junctions — falling back to a straight two-point line
        only for the synthetic placeholder grid, which has no richer shape.
        """
        features: List[dict] = []
        for u, v, data in self.graph.edges(data=True):
            shape = data.get("shape")
            if shape:
                coordinates = [[lng, lat] for lng, lat in shape]
            else:
                u_coord = self.get_node_coord(str(u))
                v_coord = self.get_node_coord(str(v))
                if u_coord is None or v_coord is None:
                    continue
                u_lat, u_lng = u_coord
                v_lat, v_lng = v_coord
                coordinates = [[u_lng, u_lat], [v_lng, v_lat]]

            features.append(
                {
                    "type": "Feature",
                    "id": data.get("edge_id", f"{u}->{v}"),
                    "properties": {
                        "edge_id": data.get("edge_id", f"{u}->{v}"),
                        "from": str(u),
                        "to": str(v),
                        "weight": round(float(data.get("weight", 0.0) or 0.0), 4),
                        "base_weight": round(float(data.get("base_weight", 0.0) or 0.0), 4),
                        "congestion": round(float(data.get("congestion", 0.0) or 0.0), 4),
                        "length_m": float(data.get("length_m", 0.0) or 0.0),
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates,
                    },
                }
            )

        bounds = self.get_graph_bounds() or {}
        return {
            "type": "FeatureCollection",
            "name": name,
            "bbox": [
                bounds.get("min_lng", 80.2101),
                bounds.get("min_lat", 13.0850),
                bounds.get("max_lng", 80.2101),
                bounds.get("max_lat", 13.0850),
            ],
            "metadata": {
                "area": "Anna Nagar, Chennai",
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                # "sumo_network" = real geometry, "synthetic_fallback" = the
                # placeholder grid (only used if the real network failed to
                # load) — see RoadNetworkGraph.initialize_graph().
                "source": self._source,
            },
            "features": features,
        }


# Module-level singleton — one live graph shared across requests within the process.
_default_graph: Optional[RoadNetworkGraph] = None


def get_road_network_graph() -> RoadNetworkGraph:
    global _default_graph
    if _default_graph is None:
        _default_graph = RoadNetworkGraph()
        _default_graph.initialize_graph()
    return _default_graph
