"""Ambulance/hospital/emergency-mission schemas.

Shapes are derived directly from app/emergency/ambulance_manager.py and
app/emergency/mission_manager.py — the real fleet and mission state
machine, not invented independently.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.models.route_models import Coordinate


class HospitalInfo(BaseModel):
    """A real hospital from app.integrations.osm_poi_loader — not invented."""

    id: str
    name: str
    location: Coordinate


class AmbulanceUnit(BaseModel):
    ambulance_id: str
    unit_number: str
    hospital_name: str
    status: str  # "available" | "dispatched" | "at_scene" | "returning"


class RoutePlanInfo(BaseModel):
    edges: List[str]
    coords: List[Coordinate]
    travel_time_s: float


class EmergencyMissionInfo(BaseModel):
    mission_id: str
    accident_id: str
    edge_id: str
    hospital_name: str
    ambulance_id: str
    unit_number: str
    state: str
    current_location: Coordinate
    outbound_route: RoutePlanInfo
    signal_priority_available: bool
    on_site_seconds_remaining: Optional[float] = None


class HospitalListResponse(BaseModel):
    hospitals: List[HospitalInfo]


class AmbulanceListResponse(BaseModel):
    units: List[AmbulanceUnit]


class MissionListResponse(BaseModel):
    missions: List[EmergencyMissionInfo]
