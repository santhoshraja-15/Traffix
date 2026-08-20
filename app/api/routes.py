"""
Aggregates all API sub-routers into a single ``api_router`` so
``app/main.py`` only needs one import.

The WebSocket endpoint at /api/realtime/{simulation_id} now lives in
``app.api.traffic`` alongside the rest of the traffic routes. It is wired in
via ``traffic.router`` below.  The old per-client tick loop that used to live
in this file has been removed — broadcasting is now the exclusive
responsibility of ``SimulationManager`` so all subscribers receive the same
consistent payload.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api import accidents, ambulance, analysis, health, navigation, simulation, traffic

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(navigation.router)
api_router.include_router(traffic.router)       # Includes WS /realtime/{simulation_id}
api_router.include_router(accidents.router)
api_router.include_router(ambulance.router)
api_router.include_router(simulation.router)
api_router.include_router(analysis.router)
