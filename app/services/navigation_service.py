"""
Navigation service.

High-level façade used by the navigation API handler. Wraps RoutingService
with additional logging and can be extended with trip-progress tracking.
"""
from __future__ import annotations

from typing import List

from app.models.route_models import CandidateRoute, RouteRequest
from app.services.routing_service import RoutingService, get_routing_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


class NavigationService:
    """Façade over RoutingService for the navigation API layer."""

    def __init__(self, routing_service: RoutingService | None = None) -> None:
        self._routing = routing_service or get_routing_service()

    def get_routes(self, request: RouteRequest) -> List[CandidateRoute]:
        """
        Resolve, route, and return candidate routes for *request*.

        Delegates fully to RoutingService; may be extended with caching,
        user-preference filtering, or logging enrichment.
        """
        logger.info(
            "NavigationService.get_routes: src=%s dest=%s mode=%s",
            request.source,
            request.destination,
            request.mode,
        )
        routes = self._routing.get_candidate_routes_for_request(request)
        logger.info("NavigationService: returned %d route(s).", len(routes))
        return routes


# Module-level singleton.
_default_nav_service: NavigationService | None = None


def get_navigation_service() -> NavigationService:
    global _default_nav_service
    if _default_nav_service is None:
        _default_nav_service = NavigationService()
    return _default_nav_service
