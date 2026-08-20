"""
Orchestrates the routing pipeline: coordinate snapping → live ML congestion
predictions → graph weight updates → k-shortest-paths → Pydantic CandidateRoute.

Coordinate snapping
-------------------
The frontend sends raw lat/lng from map clicks. ``RoutingService.snap_to_node``
converts those to graph node IDs via ``RoadNetworkGraph.get_nearest_node()``.
If the nearest node is farther than ``MAX_SNAP_DISTANCE_M`` the coordinates are
considered outside the service area and a ``CoordinateOutOfBoundsError`` is
raised so the API layer can return a clean HTTP 400.

The existing ``get_candidate_routes(source, destination, count)`` interface is
preserved unchanged so no callers that already pass explicit node IDs break.
"""
from __future__ import annotations

from typing import List, Optional

from app.integrations.existing_ml_adapter import TrafficModelAdapter, get_model_adapter
from app.models.route_models import CandidateRoute, Coordinate, RouteRequest
from app.routing.dynamic_routing import (
    NodeNotFoundError,
    NoRouteFoundError,
    PathResult,
    calculate_top_routes,
)
from app.routing.graph_manager import RoadNetworkGraph, get_road_network_graph
from app.utils.constants import CongestionLevel
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Boundary guard — if the nearest graph node is farther than this the input
# coordinates are considered "ridiculously far" from the graph service area.
# The mock grid covers ~1.5 km × 1.5 km around Chennai; 50 km is generous.
# ---------------------------------------------------------------------------
MAX_SNAP_DISTANCE_M: float = 50_000.0  # 50 km


class CoordinateOutOfBoundsError(ValueError):
    """
    Raised when a lat/lng coordinate snaps to a graph node that is too far away,
    indicating the point lies well outside the graph's service area.
    """

    def __init__(self, label: str, snap_dist_m: float) -> None:
        bounds_km = MAX_SNAP_DISTANCE_M / 1_000
        self.snap_dist_m = snap_dist_m
        self.label = label
        super().__init__(
            f"{label} coordinates are {snap_dist_m / 1_000:.1f} km from the nearest "
            f"graph node (limit: {bounds_km:.0f} km). "
            f"Ensure the map is centred on the correct city/region."
        )


def _congestion_level_from_score(score: float) -> CongestionLevel:
    if score < 0.15:
        return CongestionLevel.FREE_FLOW
    if score < 0.35:
        return CongestionLevel.LIGHT
    if score < 0.6:
        return CongestionLevel.MODERATE
    if score < 0.85:
        return CongestionLevel.HEAVY
    return CongestionLevel.SEVERE


class RoutingService:
    """Ties together coordinate snapping, the ML adapter, graph manager, and pathfinding."""

    def __init__(
        self,
        graph_manager: Optional[RoadNetworkGraph] = None,
        model_adapter: Optional[TrafficModelAdapter] = None,
    ) -> None:
        self._graph_manager = graph_manager or get_road_network_graph()
        self._model_adapter = model_adapter or get_model_adapter()

    # ------------------------------------------------------------------
    # Coordinate snapping
    # ------------------------------------------------------------------

    def snap_to_node(
        self,
        lat: float,
        lon: float,
        label: str = "Coordinate",
    ) -> str:
        """
        Snap *(lat, lon)* to the nearest graph node and return its node ID.

        Raises:
            CoordinateOutOfBoundsError: if the nearest node is farther than
                ``MAX_SNAP_DISTANCE_M`` metres, meaning the point is outside
                the graph's service area.
        """
        node_id, dist_m = self._graph_manager.get_nearest_node(lat, lon)

        if dist_m > MAX_SNAP_DISTANCE_M:
            bounds = self._graph_manager.get_graph_bounds()
            logger.warning(
                "Snap out-of-bounds: %s (%.5f, %.5f) snapped to '%s' dist=%.0f m  "
                "graph_bounds=%s",
                label,
                lat,
                lon,
                node_id,
                dist_m,
                bounds,
            )
            raise CoordinateOutOfBoundsError(label, dist_m)

        logger.debug(
            "Snapped %s (%.5f, %.5f) → node '%s'  dist=%.1f m",
            label,
            lat,
            lon,
            node_id,
            dist_m,
        )
        return node_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_congestion_weights(self) -> None:
        """Pull current edge features, get live ML predictions, push weights back to the graph."""
        edge_rows = self._graph_manager.get_edge_feature_rows()
        predictions = self._model_adapter.predict_congestion(edge_rows)
        self._graph_manager.update_edge_weights(predictions)

    def _to_candidate_route(self, result: PathResult) -> CandidateRoute:
        coords: List[Coordinate] = []
        for node_id in result.node_path:
            coord = self._graph_manager.get_node_coord(node_id)
            if coord is not None:
                lat, lng = coord
                coords.append(Coordinate(lat=lat, lng=lng))

        return CandidateRoute(
            route_id=f"route-{result.rank}",
            rank=result.rank,
            travel_time=round(result.total_travel_time, 2),
            distance=round(result.total_distance_m, 2),
            traffic_level=round(result.avg_congestion, 3),
            congestion_level=_congestion_level_from_score(result.avg_congestion),
            edges=result.edge_ids,
            coords=coords,
        )

    # ------------------------------------------------------------------
    # Public routing API
    # ------------------------------------------------------------------

    def get_candidate_routes(
        self,
        source: str,
        destination: str,
        count: int = 3,
    ) -> List[CandidateRoute]:
        """
        Full pipeline for one routing request given explicit node IDs.

        Preserved unchanged so any callers that already resolve node IDs
        (e.g. tests, admin tools) are not broken by the snapping addition.

        Raises NodeNotFoundError / NoRouteFoundError on bad input — the API
        layer maps these to HTTP 404/400.
        """
        if not self._graph_manager.is_initialized:
            self._graph_manager.initialize_graph()

        self._refresh_congestion_weights()

        path_results = calculate_top_routes(
            self._graph_manager.graph,
            source,
            destination,
            count=count,
        )
        return [self._to_candidate_route(r) for r in path_results]

    def get_candidate_routes_for_request(
        self,
        request: RouteRequest,
    ) -> List[CandidateRoute]:
        """
        Resolve source and destination from a ``RouteRequest``, then route.

        Resolution priority (per endpoint):
          1. Use ``source_node_id`` / ``destination_node_id`` if provided.
          2. Otherwise snap ``source.lat/lng`` / ``destination.lat/lng`` to the
             nearest graph node via Haversine nearest-neighbour search.

        Raises:
            CoordinateOutOfBoundsError: coordinates snap to a node > 50 km away.
            NodeNotFoundError: a provided node ID does not exist in the graph.
            NoRouteFoundError: source and destination are disconnected.
        """
        if not self._graph_manager.is_initialized:
            self._graph_manager.initialize_graph()

        # --- Resolve source ---
        if request.source_node_id:
            source_node = request.source_node_id
            logger.debug("Source: using explicit node_id '%s'", source_node)
        else:
            source_node = self.snap_to_node(
                request.source.lat, request.source.lng, label="Source"
            )

        # --- Resolve destination ---
        if request.destination_node_id:
            dest_node = request.destination_node_id
            logger.debug("Destination: using explicit node_id '%s'", dest_node)
        else:
            dest_node = self.snap_to_node(
                request.destination.lat, request.destination.lng, label="Destination"
            )

        logger.info(
            "Routing %s -> %s  (alternatives=%d)",
            source_node,
            dest_node,
            request.alternatives,
        )
        return self.get_candidate_routes(source_node, dest_node, count=request.alternatives)


# ---------------------------------------------------------------------------
# Module-level singleton — graph/model are not re-initialized per request.
# ---------------------------------------------------------------------------
_default_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    global _default_service
    if _default_service is None:
        _default_service = RoutingService()
    return _default_service
