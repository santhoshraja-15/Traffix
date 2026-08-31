"""Simulation status/control schemas.

Shapes are derived directly from how ``app/api/simulation.py`` and
``app/core/simulation_manager.py`` already construct and consume these
objects (see ``FRONTEND_AUDIT.md`` — the real tick loop and status endpoints
were already written against this contract; only the Pydantic schemas
themselves were unimplemented stubs).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.utils.constants import ScenarioType, SimulationStatus


class SimulationConfig(BaseModel):
    scenario_type: ScenarioType = ScenarioType.DEMAND_SPIKE
    location: Optional[str] = None
    vehicle_density: float = Field(default=0.5, ge=0.0, le=1.0)
    rainfall: float = Field(default=0.0, ge=0.0, le=1.0)
    accident_flag: bool = False


class SimulationStartRequest(BaseModel):
    simulation_id: Optional[str] = None
    config: SimulationConfig = Field(default_factory=SimulationConfig)


class SimulationStartResponse(BaseModel):
    simulation_id: str
    status: SimulationStatus


class SimulationStatusResponse(BaseModel):
    simulation_id: str
    status: SimulationStatus
    tick: int
    elapsed_seconds: float
    active_vehicles: int


class ScenarioInjectionResponse(BaseModel):
    simulation_id: str
    scenario_type: ScenarioType
    accepted: bool


class SimulationPauseStateResponse(BaseModel):
    """
    Real pause/resume/step response — deliberately its own minimal shape
    rather than reusing SimulationStatusResponse, which carries an
    active_vehicles estimate that isn't derived from real per-tick data
    (a pre-existing gap, out of scope for this endpoint). Every field here
    is genuinely real: current tick count and whether the loop is paused,
    both read straight from SimulationManager's own state.
    """

    simulation_id: str
    paused: bool
    tick: int
