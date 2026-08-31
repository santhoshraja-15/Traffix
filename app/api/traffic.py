"""
Live traffic state endpoints + real-time WebSocket stream.

The WebSocket endpoint at /api/realtime/{simulation_id} accepts client
connections and registers them with the module-level ``websocket_manager``.
All tick data is pushed by ``SimulationManager``'s background loop — the
client-side receive loop here only keeps the connection alive and handles
graceful disconnect; it never sends data itself.  This guarantees that every
client subscribed to the same simulation_id receives the exact same broadcast
payload with no per-client timing drift.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import websocket_manager
from app.models.traffic_models import TrafficUpdate
from app.services.traffic_service import get_traffic_service
from app.utils.constants import UpdateType
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["traffic"])


@router.get("/traffic/{edge_id}", response_model=TrafficUpdate)
async def get_traffic_state(edge_id: str) -> TrafficUpdate:
    """
    Real point-in-time snapshot of *edge_id*'s traffic state, from
    traffic_state_store (populated every tick by SimulationManager — see
    app/core/simulation_manager.py). 404s honestly if the edge hasn't been
    seen yet (unknown edge_id, or no simulation has run) rather than
    returning a plausible-looking fake value.
    """
    state = get_traffic_service().get_edge_state(edge_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"No live traffic state for edge '{edge_id}' — start a simulation first.",
        )
    return TrafficUpdate(
        type=UpdateType.TRAFFIC,
        edge_id=state.edge_id,
        speed=state.speed,
        vehicle_count=state.vehicle_count,
        congestion=state.congestion_level,
    )


@router.websocket("/realtime/{simulation_id}")
async def realtime_updates(websocket: WebSocket, simulation_id: str) -> None:
    """
    Stream real-time traffic updates for *simulation_id*.

    On connect: the socket is accepted and registered with ConnectionManager so
    the SimulationManager broadcast loop can fan-out to it.

    The receive loop below simply waits for client messages (ping/close frames).
    Actual data is pushed by SimulationManager every ~1 second via
    ``websocket_manager.broadcast()``.

    On disconnect: the socket is cleanly removed from ConnectionManager.
    """
    await websocket_manager.connect(simulation_id, websocket)
    logger.info(
        "WebSocket connected: simulation_id=%s  total_clients=%d",
        simulation_id,
        websocket_manager.connection_count(simulation_id),
    )
    try:
        # Keep the connection open. The SimulationManager loop drives all sends.
        # receive_text() will raise WebSocketDisconnect when the client closes.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: simulation_id=%s", simulation_id)
    finally:
        websocket_manager.disconnect(simulation_id, websocket)
        logger.debug(
            "WebSocket removed: simulation_id=%s  remaining_clients=%d",
            simulation_id,
            websocket_manager.connection_count(simulation_id),
        )
