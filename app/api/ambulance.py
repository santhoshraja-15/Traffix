"""Ambulance dispatch / green-corridor endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.models.ambulance_models import (
    AmbulanceDispatchRequest,
    AmbulanceDispatchResponse,
    AmbulanceStatus,
)

router = APIRouter(tags=["ambulance"])


@router.post("/ambulance/dispatch", response_model=AmbulanceDispatchResponse)
async def dispatch_ambulance(request: AmbulanceDispatchRequest) -> AmbulanceDispatchResponse:
    status = AmbulanceStatus(
        ambulance_id=str(uuid.uuid4()),
        current_location=request.origin,
        destination=request.destination,
        route_edges=["edge-0", "edge-1", "edge-2"],
        green_corridor_active=True,
        eta_seconds=420,
    )
    return AmbulanceDispatchResponse(ambulance=status)
