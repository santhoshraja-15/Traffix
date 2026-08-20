"""
Simulation lifecycle manager.

Owns the background async tick loop for each running simulation. On every tick
(once per second) it:
  1. Mutates mock sensor readings on the RoadNetworkGraph edges.
  2. Calls TrafficModelAdapter to produce congestion predictions.
  3. Applies those predictions back to the graph via update_edge_weights().
  4. Broadcasts a TrafficUpdate-compatible JSON payload to all subscribed
     WebSocket clients via ConnectionManager.

``await asyncio.sleep(1)`` at the end of every tick yields control back to the
FastAPI event loop so HTTP requests are never blocked.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.websocket_manager import websocket_manager
from app.integrations.existing_ml_adapter import TrafficModelAdapter, get_model_adapter
from app.models.simulation_models import SimulationConfig
from app.routing.graph_manager import RoadNetworkGraph, get_road_network_graph
from app.utils.constants import CongestionLevel, SimulationStatus, UpdateType
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Map congestion probability → CongestionLevel label for the broadcast payload.
def _congestion_label(score: float) -> str:
    if score < 0.2:
        return CongestionLevel.FREE_FLOW.value
    if score < 0.4:
        return CongestionLevel.LIGHT.value
    if score < 0.6:
        return CongestionLevel.MODERATE.value
    if score < 0.8:
        return CongestionLevel.HEAVY.value
    return CongestionLevel.SEVERE.value


class SimulationManager:
    """Manages async background tick loops keyed by simulation_id."""

    def __init__(self) -> None:
        # Active asyncio tasks — one per simulation.
        self._tasks: Dict[str, asyncio.Task[None]] = {}
        # Per-simulation tick counter.
        self._tick_counts: Dict[str, int] = {}
        # Track the config each simulation was started with (used for rainfall etc.).
        self._configs: Dict[str, SimulationConfig] = {}

    # ------------------------------------------------------------------
    # Public lifecycle API
    # ------------------------------------------------------------------

    def start(self, simulation_id: str, config: SimulationConfig) -> None:
        """
        Spawn a background asyncio task for *simulation_id*.

        Safe to call even if a loop is already running for that id — the old
        task is cancelled first so there are never two loops competing.
        """
        if simulation_id in self._tasks:
            logger.warning(
                "Simulation %s already running — cancelling old loop before restart.",
                simulation_id,
            )
            self.stop(simulation_id)

        self._configs[simulation_id] = config
        self._tick_counts[simulation_id] = 0

        task: asyncio.Task[None] = asyncio.create_task(
            self._run_simulation_loop(simulation_id),
            name=f"sim-loop-{simulation_id}",
        )
        self._tasks[simulation_id] = task
        task.add_done_callback(lambda t: self._on_task_done(simulation_id, t))
        logger.info("Simulation %s started.", simulation_id)

    def stop(self, simulation_id: str) -> None:
        """Cancel the background loop for *simulation_id* if it exists."""
        task = self._tasks.pop(simulation_id, None)
        if task and not task.done():
            task.cancel()
            logger.info("Simulation %s cancelled.", simulation_id)
        self._tick_counts.pop(simulation_id, None)
        self._configs.pop(simulation_id, None)

    def stop_all(self) -> None:
        """Cancel every active simulation — called during server shutdown."""
        ids = list(self._tasks.keys())
        for simulation_id in ids:
            self.stop(simulation_id)
        logger.info("All simulation tasks cancelled (%d total).", len(ids))

    @property
    def active_simulations(self) -> list[str]:
        return list(self._tasks.keys())

    def tick_count(self, simulation_id: str) -> int:
        return self._tick_counts.get(simulation_id, 0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_task_done(self, simulation_id: str, task: asyncio.Task[None]) -> None:
        """Clean up registry entries when a task finishes or is cancelled."""
        self._tasks.pop(simulation_id, None)
        if task.cancelled():
            logger.debug("Simulation %s task was cancelled (expected on shutdown).", simulation_id)
        elif task.exception():
            logger.error(
                "Simulation %s task exited with error: %s",
                simulation_id,
                task.exception(),
            )

    def _mutate_edge_sensor_data(
        self,
        graph: RoadNetworkGraph,
        config: SimulationConfig,
    ) -> None:
        """
        Inject randomised mock sensor readings into each graph edge so the ML
        adapter has fresh feature data on every tick.

        In production this would be replaced by real telemetry ingestion
        (e.g. SUMO TraCI readings or a Kafka consumer). For the hackathon demo
        we jitter the previous values so the UI shows plausible movement.
        """
        density = config.vehicle_density  # 0.0 – 1.0
        rainfall = config.rainfall  # 0.0 – 1.0
        accident_active = config.accident_flag

        for u, v, data in graph.graph.edges(data=True):
            capacity: float = float(data.get("capacity", 120))

            # Vehicle count scales with density + some randomness.
            base_vehicles = density * capacity
            jitter = random.uniform(-0.15, 0.15) * capacity
            if accident_active:
                jitter -= 0.1 * capacity  # accidents reduce throughput upstream
            vehicle_count = max(0, min(capacity * 1.5, base_vehicles + jitter))

            # Average speed inversely proportional to occupancy, further reduced by rain.
            occupancy = vehicle_count / max(1.0, capacity)
            avg_speed = max(5.0, 60.0 * (1.0 - occupancy) * (1.0 - rainfall * 0.4))

            data["vehicle_count"] = int(vehicle_count)
            data["avg_speed"] = round(avg_speed, 2)
            data["rainfall"] = rainfall

    async def _run_simulation_loop(self, simulation_id: str) -> None:
        """
        Main simulation tick loop.

        Structured to yield control back to the event loop via
        ``await asyncio.sleep(1)`` at the **end** of every iteration, ensuring
        FastAPI can serve HTTP/WebSocket requests between ticks.
        """
        graph: RoadNetworkGraph = get_road_network_graph()
        adapter: TrafficModelAdapter = get_model_adapter()
        config: SimulationConfig = self._configs[simulation_id]

        logger.info("Simulation %s: tick loop started.", simulation_id)

        try:
            while True:
                tick = self._tick_counts[simulation_id]

                # 1. Inject fresh mock sensor data into the graph edges.
                self._mutate_edge_sensor_data(graph, config)

                # 2. Get congestion predictions from the ML adapter (or heuristic fallback).
                edge_rows = graph.get_edge_feature_rows()
                predictions: Dict[str, float] = adapter.predict_congestion(edge_rows)

                # 3. Apply predictions back to the graph's live weights.
                updated_count = graph.update_edge_weights(predictions)

                # 4. Build a representative broadcast payload (first few edges as sample).
                sample_rows = edge_rows[:5]  # broadcast a sample; full data is in the graph
                traffic_events: list[Dict[str, Any]] = []
                for row in sample_rows:
                    edge_id: str = str(row.get("edge_id", "unknown"))
                    congestion_score = predictions.get(edge_id, 0.0)
                    traffic_events.append(
                        {
                            "type": UpdateType.TRAFFIC.value,
                            "edge_id": edge_id,
                            "speed": round(float(row.get("avg_speed", 40.0)), 1),
                            "vehicle_count": int(row.get("vehicle_count", 0)),
                            "congestion": _congestion_label(congestion_score),
                            "congestion_score": round(congestion_score, 4),
                        }
                    )

                payload: Dict[str, Any] = {
                    "type": UpdateType.TRAFFIC.value,
                    "simulation_id": simulation_id,
                    "status": SimulationStatus.RUNNING.value,
                    "tick": tick,
                    "edges_updated": updated_count,
                    "traffic": traffic_events,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # 5. Fan-out to all subscribed WebSocket clients for this simulation.
                await websocket_manager.broadcast(simulation_id, payload)

                logger.debug(
                    "Simulation %s tick=%d  edges_updated=%d  ws_clients=%d",
                    simulation_id,
                    tick,
                    updated_count,
                    websocket_manager.connection_count(simulation_id),
                )

                self._tick_counts[simulation_id] = tick + 1

                # ---------------------------------------------------------------
                # IMPORTANT: yield control back to the FastAPI event loop so that
                # HTTP requests are not starved between simulation ticks.
                # ---------------------------------------------------------------
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            # Normal shutdown path — log and exit cleanly.
            logger.info(
                "Simulation %s: tick loop cancelled at tick %d.",
                simulation_id,
                self._tick_counts.get(simulation_id, 0),
            )
            raise  # Re-raise so asyncio marks the task as properly cancelled.

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Simulation %s: unexpected error in tick loop: %s",
                simulation_id,
                exc,
                exc_info=True,
            )
            raise


# ---------------------------------------------------------------------------
# Module-level singleton — shared across the entire FastAPI process.
# ---------------------------------------------------------------------------
simulation_manager = SimulationManager()
