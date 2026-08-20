"""
Routing / navigation endpoints — serves live, ML-weighted candidate routes.

Source / destination resolution order
--------------------------------------
1. If the request includes ``source_node_id`` / ``destination_node_id``, those
   are used directly (backward-compatible with existing callers / tests).
2. Otherwise the raw ``source.lat`` / ``source.lng`` (and destination) fields
   are snapped to the nearest graph node via Haversine nearest-neighbour search
   inside ``RoutingService.get_candidate_routes_for_request()``.
3. If the snapped node is farther than 50 km the endpoint returns HTTP 400
   (coordinates out of the graph's service area).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.route_models import RouteRequest, RouteResponse
from app.routing.dynamic_routing import NodeNotFoundError, NoRouteFoundError
from app.services.routing_service import (
    CoordinateOutOfBoundsError,
    RoutingService,
    get_routing_service,
)

router = APIRouter(tags=["navigation"])


@router.post("/routes", response_model=RouteResponse)
async def get_routes(
    request: RouteRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteResponse:
    """
    Return up to ``alternatives`` candidate routes between source and destination.

    Accepts either:
    - Explicit graph node IDs (``source_node_id`` / ``destination_node_id``), **or**
    - Raw lat/lng coordinates (``source`` / ``destination``) — automatically
      snapped to the nearest graph node.

    Both fields are accepted simultaneously; node IDs take priority when present.
    """
    try:
        routes = service.get_candidate_routes_for_request(request)

    except CoordinateOutOfBoundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except NodeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except NoRouteFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return RouteResponse(request_id=str(uuid.uuid4()), routes=routes)
