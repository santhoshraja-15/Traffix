"""Accident/incident schemas.

Shapes are derived directly from how app/api/accidents.py and
app/services/accident_service.py construct and consume these objects.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.models.route_models import Coordinate


class AccidentCreateRequest(BaseModel):
    edge_id: str
    location: Optional[Coordinate] = None
    severity: str = "moderate"  # low | medium | high | critical (also accepts minor/moderate)
    lanes_blocked: int = 1


class AccidentReport(BaseModel):
    accident_id: str
    edge_id: str
    location: Optional[Coordinate] = None
    severity: str = "moderate"
    lanes_blocked: int = 1
    # Real values resolved server-side from the loaded network graph — see
    # AccidentService.report_accident(). road_name is "" if the edge has no
    # real OSM name (see sumo_network_loader.py's ~44%-of-edges coverage).
    road_name: str = ""
    status: str = "active"  # "active" | "resolved"


class AccidentResponse(BaseModel):
    accident: AccidentReport


class AccidentListResponse(BaseModel):
    accidents: List[AccidentReport]


class AccidentResolveResponse(BaseModel):
    accident_id: str
    resolved: bool
