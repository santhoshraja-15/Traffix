"""Route/candidate/score schemas.

Shapes are derived directly from how ``RoutingService``/``NavigationService``
(``app/services/routing_service.py``, ``app/services/navigation_service.py``)
and the ``/api/routes`` endpoint (``app/api/navigation.py``) already construct
and consume these objects — see ``FRONTEND_AUDIT.md`` for the audit that
uncovered these were still unimplemented stubs.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.constants import CongestionLevel, TravelMode


class Coordinate(BaseModel):
    """A WGS84 lat/lng point (matches the frontend's coordinate convention)."""

    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)


class RouteRequest(BaseModel):
    """
    Source/destination may be given as explicit graph node IDs OR raw
    lat/lng coordinates (auto-snapped to the nearest graph node) — both are
    accepted simultaneously; node IDs take priority when present. See
    ``RoutingService.get_candidate_routes_for_request``.
    """

    source_node_id: Optional[str] = None
    destination_node_id: Optional[str] = None
    source: Optional[Coordinate] = None
    destination: Optional[Coordinate] = None
    alternatives: int = Field(default=3, ge=1, le=10)
    mode: TravelMode = TravelMode.DRIVING


class CandidateRoute(BaseModel):
    """One ranked candidate route, resolved against the live routing graph."""

    route_id: str
    rank: int
    travel_time: float  # seconds, congestion-adjusted
    distance: float  # meters
    traffic_level: float  # average congestion score across the route, 0.0-1.0
    congestion_level: CongestionLevel
    edges: List[str]
    coords: List[Coordinate]


class RouteResponse(BaseModel):
    request_id: str
    routes: List[CandidateRoute]
