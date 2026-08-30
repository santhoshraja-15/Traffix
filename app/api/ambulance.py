"""
Ambulance/hospital/emergency-mission endpoints.

Missions are dispatched automatically the moment a real accident is
reported (see app/services/accident_service.py) — there's no separate
manual "dispatch" trigger, matching MASTER_PROMPT.md's "whenever an active
accident is detected, automatically run a full simulated emergency
response." These endpoints expose the resulting real state for clients
that (re)connect mid-mission; the live per-tick state also broadcasts over
the WebSocket (see app/core/simulation_manager.py).
"""
from __future__ import annotations

from fastapi import APIRouter

from app.emergency.ambulance_manager import ambulance_manager
from app.emergency.mission_manager import mission_manager
from app.integrations.osm_poi_loader import get_real_hospitals
from app.models.ambulance_models import (
    AmbulanceListResponse,
    AmbulanceUnit,
    Coordinate,
    EmergencyMissionInfo,
    HospitalInfo,
    HospitalListResponse,
    MissionListResponse,
    RoutePlanInfo,
)

router = APIRouter(tags=["ambulance"])


@router.get("/emergency/hospitals", response_model=HospitalListResponse)
async def list_hospitals() -> HospitalListResponse:
    """Real hospitals in the Anna Nagar area (see app/integrations/osm_poi_loader.py)."""
    hospitals = get_real_hospitals()
    return HospitalListResponse(
        hospitals=[
            HospitalInfo(id=h.osm_id, name=h.name, location=Coordinate(lat=h.lat, lng=h.lng))
            for h in hospitals
        ]
    )


@router.get("/ambulance/units", response_model=AmbulanceListResponse)
async def list_ambulance_units() -> AmbulanceListResponse:
    """The real ambulance fleet — one unit per real hospital, seeded on first use."""
    ambulance_manager.ensure_seeded()
    return AmbulanceListResponse(
        units=[
            AmbulanceUnit(
                ambulance_id=u.ambulance_id,
                unit_number=u.unit_number,
                hospital_name=u.hospital_name,
                status=u.status,
            )
            for u in ambulance_manager.all_units()
        ]
    )


@router.get("/emergency/missions", response_model=MissionListResponse)
async def list_active_missions() -> MissionListResponse:
    """Active emergency missions — for a client that (re)connects mid-mission."""
    from app.core.simulation_manager import simulation_manager  # noqa: PLC0415

    # Best-effort "now" for a REST snapshot outside the tick loop — the
    # live WebSocket broadcast (which drives the actual UI) always uses
    # the real current tick of the simulation it's broadcasting for.
    ids = simulation_manager.active_simulations
    current_tick = simulation_manager.tick_count(ids[0]) if ids else 0

    missions = []
    for m in mission_manager.active_missions():
        lat, lng = mission_manager.current_position(m, current_tick)
        on_site_remaining = None
        if m.on_site_until_tick is not None:
            on_site_remaining = max(0.0, m.on_site_until_tick - current_tick)
        missions.append(
            EmergencyMissionInfo(
                mission_id=m.mission_id,
                accident_id=m.accident_id,
                edge_id=m.edge_id,
                hospital_name=m.hospital_name,
                ambulance_id=m.ambulance_id,
                unit_number=m.unit_number,
                state=m.state.value,
                current_location=Coordinate(lat=lat, lng=lng),
                outbound_route=RoutePlanInfo(
                    edges=m.outbound.edges,
                    coords=[Coordinate(lat=c[0], lng=c[1]) for c in m.outbound.coords],
                    travel_time_s=m.outbound.travel_time_s,
                ),
                signal_priority_available=m.signal_priority_available,
                on_site_seconds_remaining=on_site_remaining,
            )
        )
    return MissionListResponse(missions=missions)
