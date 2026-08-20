"""Accident reporting endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.models.accident_models import (
    AccidentCreateRequest,
    AccidentReport,
    AccidentResponse,
)

router = APIRouter(tags=["accidents"])


@router.post("/accidents", response_model=AccidentResponse)
async def report_accident(request: AccidentCreateRequest) -> AccidentResponse:
    accident = AccidentReport(
        accident_id=str(uuid.uuid4()),
        edge_id=request.edge_id,
        location=request.location,
        severity=request.severity,
        lanes_blocked=request.lanes_blocked,
    )
    return AccidentResponse(accident=accident)
