"""Accident reporting endpoints — wired to the real AccidentService."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.accident_models import (
    AccidentCreateRequest,
    AccidentListResponse,
    AccidentReport,
    AccidentResolveResponse,
    AccidentResponse,
)
from app.models.route_models import Coordinate
from app.services.accident_service import get_accident_service

router = APIRouter(tags=["accidents"])


@router.post("/accidents", response_model=AccidentResponse)
async def report_accident(request: AccidentCreateRequest) -> AccidentResponse:
    """
    Report a real accident on *edge_id* — applies a genuine capacity
    reduction to that edge (see AccidentService), which the next simulation
    tick's congestion/risk scoring will reflect for real.
    """
    service = get_accident_service()
    result = service.report_accident(
        edge_id=request.edge_id,
        severity=request.severity,
        location_description="",
    )
    location = result["location"]
    accident = AccidentReport(
        accident_id=result["accident_id"],
        edge_id=result["edge_id"],
        location=Coordinate(**location) if location else request.location,
        severity=result["severity"],
        lanes_blocked=request.lanes_blocked,
        road_name=result["road_name"],
        status=result["status"],
    )
    return AccidentResponse(accident=accident)


@router.get("/accidents", response_model=AccidentListResponse)
async def list_active_accidents() -> AccidentListResponse:
    """Currently active accidents — for a client that (re)connects mid-simulation."""
    service = get_accident_service()
    from app.routing.graph_manager import get_road_network_graph  # noqa: PLC0415

    graph = get_road_network_graph()
    accidents = []
    for record in service.active_accidents():
        location = graph.get_edge_midpoint(record.edge_id)
        accidents.append(
            AccidentReport(
                accident_id=record.accident_id,
                edge_id=record.edge_id,
                location=Coordinate(lat=location[0], lng=location[1]) if location else None,
                severity=record.severity,
                road_name=graph.get_edge_name(record.edge_id),
                status="active",
            )
        )
    return AccidentListResponse(accidents=accidents)


@router.post("/accidents/{accident_id}/resolve", response_model=AccidentResolveResponse)
async def resolve_accident(accident_id: str) -> AccidentResolveResponse:
    """Mark an accident resolved and restore the affected edge's real capacity."""
    service = get_accident_service()
    resolved = service.resolve_accident(accident_id)
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Accident '{accident_id}' not found.")
    return AccidentResolveResponse(accident_id=accident_id, resolved=True)
