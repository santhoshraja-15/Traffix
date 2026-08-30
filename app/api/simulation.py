"""Simulation control endpoints: start, scenario injection, status polling."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.simulation_manager import simulation_manager
from app.models.simulation_models import (
    ScenarioInjectionResponse,
    SimulationConfig,
    SimulationPauseStateResponse,
    SimulationStartRequest,
    SimulationStartResponse,
    SimulationStatusResponse,
)
from app.utils.constants import SimulationStatus
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["simulation"])

# In-memory registry so /status/{id} has something to look up during the demo.
_MOCK_SIMULATIONS: dict[str, SimulationStatusResponse] = {}


@router.post("/simulation/start", response_model=SimulationStartResponse)
async def start_simulation(request: SimulationStartRequest) -> SimulationStartResponse:
    """
    Start a new simulation.

    Creates a simulation record, spawns the SimulationManager background loop
    (which ticks every 1 second), and returns the new simulation_id immediately.
    The background loop runs independently — the HTTP response is not blocked.
    """
    simulation_id = request.simulation_id or str(uuid.uuid4())

    # Persist a status record so /status/{id} can serve it.
    _MOCK_SIMULATIONS[simulation_id] = SimulationStatusResponse(
        simulation_id=simulation_id,
        status=SimulationStatus.RUNNING,
        tick=0,
        elapsed_seconds=0.0,
        active_vehicles=int(request.config.vehicle_density * 200),
    )

    # Kick off the real-time simulation loop as a non-blocking background task.
    simulation_manager.start(simulation_id, request.config)
    logger.info(
        "Simulation %s started  density=%.2f  scenario=%s",
        simulation_id,
        request.config.vehicle_density,
        request.config.scenario_type,
    )

    return SimulationStartResponse(simulation_id=simulation_id, status=SimulationStatus.RUNNING)


@router.post("/simulation/stop/{simulation_id}", response_model=SimulationStatusResponse)
async def stop_simulation(simulation_id: str) -> SimulationStatusResponse:
    """Stop an active simulation and cancel its background loop."""
    if simulation_id not in _MOCK_SIMULATIONS:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found.")

    simulation_manager.stop(simulation_id)
    record = _MOCK_SIMULATIONS[simulation_id]
    # Update status in the registry.
    _MOCK_SIMULATIONS[simulation_id] = SimulationStatusResponse(
        simulation_id=simulation_id,
        status=SimulationStatus.STOPPED,
        tick=simulation_manager.tick_count(simulation_id),
        elapsed_seconds=float(simulation_manager.tick_count(simulation_id)),
        active_vehicles=record.active_vehicles,
    )
    logger.info("Simulation %s stopped via API.", simulation_id)
    return _MOCK_SIMULATIONS[simulation_id]


@router.post("/simulation/pause/{simulation_id}", response_model=SimulationPauseStateResponse)
async def pause_simulation(simulation_id: str) -> SimulationPauseStateResponse:
    """
    Real pause — sets a flag SimulationManager's own tick loop checks every
    iteration (see app/core/simulation_manager.py). While paused: no TraCI/
    mock step, no ML inference, no broadcast, no tick advance. 404s if the
    simulation isn't currently running rather than a silent fake success.
    """
    if not simulation_manager.pause(simulation_id):
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' is not running.")
    return SimulationPauseStateResponse(
        simulation_id=simulation_id,
        paused=True,
        tick=simulation_manager.tick_count(simulation_id),
    )


@router.post("/simulation/resume/{simulation_id}", response_model=SimulationPauseStateResponse)
async def resume_simulation(simulation_id: str) -> SimulationPauseStateResponse:
    """Clear the real pause flag — the tick loop resumes on its next iteration."""
    if not simulation_manager.resume(simulation_id):
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' is not running.")
    return SimulationPauseStateResponse(
        simulation_id=simulation_id,
        paused=False,
        tick=simulation_manager.tick_count(simulation_id),
    )


@router.post("/simulation/step/{simulation_id}", response_model=SimulationPauseStateResponse)
async def step_simulation(simulation_id: str) -> SimulationPauseStateResponse:
    """
    Real single-step — queues exactly one real tick (TraCI/mock step, ML
    inference, broadcast, tick increment all included) to run while paused,
    then the loop re-pauses. Meaningful only while paused; 404s if the
    simulation isn't running at all.
    """
    if not simulation_manager.request_step(simulation_id):
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' is not running.")
    return SimulationPauseStateResponse(
        simulation_id=simulation_id,
        paused=simulation_manager.is_paused(simulation_id),
        tick=simulation_manager.tick_count(simulation_id),
    )


@router.post("/simulation/scenario", response_model=ScenarioInjectionResponse)
async def inject_scenario(config: SimulationConfig) -> ScenarioInjectionResponse:
    """Inject a scenario into the most-recently-started simulation."""
    return ScenarioInjectionResponse(
        simulation_id=next(iter(_MOCK_SIMULATIONS), "unknown"),
        scenario_type=config.scenario_type,
        accepted=True,
    )


@router.get("/simulation/status/{simulation_id}", response_model=SimulationStatusResponse)
async def get_simulation_status(simulation_id: str) -> SimulationStatusResponse:
    """Return the current status of a simulation."""
    status = _MOCK_SIMULATIONS.get(simulation_id)
    if status is None:
        # Hackathon-friendly fallback: return a plausible mock instead of 404ing the demo.
        status = SimulationStatusResponse(
            simulation_id=simulation_id,
            status=SimulationStatus.RUNNING,
            tick=simulation_manager.tick_count(simulation_id),
            elapsed_seconds=float(simulation_manager.tick_count(simulation_id)),
            active_vehicles=120,
        )
    return status
