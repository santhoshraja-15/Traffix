"""Accident/incident schemas.

Shapes are derived directly from how ``app/api/accidents.py`` already
constructs and consumes these objects. See ``FRONTEND_AUDIT.md`` §1.4 —
this endpoint is a stub that doesn't yet call the real ``AccidentService``/
``app/emergency`` pipeline; that rewiring is separate, later work. This file
only supplies the missing request/response schemas so the module imports.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.route_models import Coordinate


class AccidentCreateRequest(BaseModel):
    edge_id: str
    location: Optional[Coordinate] = None
    severity: str = "moderate"  # "minor" | "moderate" | "critical" — matches AccidentManager
    lanes_blocked: int = 1


class AccidentReport(BaseModel):
    accident_id: str
    edge_id: str
    location: Optional[Coordinate] = None
    severity: str = "moderate"
    lanes_blocked: int = 1


class AccidentResponse(BaseModel):
    accident: AccidentReport
