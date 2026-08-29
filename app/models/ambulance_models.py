"""Ambulance/hospital schemas.

Shapes are derived directly from how ``app/api/ambulance.py`` already
constructs and consumes these objects. See ``FRONTEND_AUDIT.md`` §1.4 —
this endpoint is a stub that doesn't yet call the real ``AmbulanceService``/
``app/emergency`` pipeline; that rewiring is separate, later work. This file
only supplies the missing request/response schemas so the module imports.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.models.route_models import Coordinate


class AmbulanceDispatchRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate


class AmbulanceStatus(BaseModel):
    ambulance_id: str
    current_location: Coordinate
    destination: Coordinate
    route_edges: List[str]
    green_corridor_active: bool = False
    eta_seconds: int = 0


class AmbulanceDispatchResponse(BaseModel):
    ambulance: AmbulanceStatus
