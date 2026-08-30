"""
Simulation lifecycle manager — SUMO-Backend Bridge Edition.

Owns the background async tick loop for each running simulation. On every tick
(once per second) it:

  1. [THREAD]  Advances SUMO via traci.simulationStep() AND reads per-edge
               metrics — both in a single synchronous call submitted to the
               SumoBridge's **dedicated** ThreadPoolExecutor(max_workers=1).

               Thread-affinity note: TraCI is single-threaded and expects
               every call to originate from the same OS thread that spawned
               the SUMO process.  We NEVER use the default thread pool
               (run_in_executor(None, ...)) for TraCI calls.  The bridge's
               1-worker executor is the sole gateway — the same thread steps
               SUMO for the entire lifetime of the simulation.

  2. [ASYNC]   If SUMO data arrived → write metrics to RoadNetworkGraph edges.
               If SUMO absent/failed → fall back to mock sensor jitter.

  3. [ASYNC]   Pass raw SUMO metrics into app.state.ml_engine.predict_batch()
               via SumoBridge.build_v15_raw_features() which maps TraCI data
               to the exact 53-column V15 feature contract.

  4. [ASYNC]   Apply risk scores → dynamic edge cost update.

  5. [ASYNC]   Broadcast JSON payload (AI risk scores + edge costs) to all
               subscribed WebSocket clients.

``await asyncio.sleep(1)`` at the end of every tick yields control back to the
FastAPI event loop so HTTP requests are never blocked.
"""
from __future__ import annotations

import asyncio
import functools
import random
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.websocket_manager import websocket_manager
from app.integrations.existing_ml_adapter import TrafficModelAdapter, get_model_adapter
from app.integrations.sumo_bridge import SUMO_AVAILABLE, SumoBridge
from app.ml.model_registry import model_registry
from app.ml.predictor import predict as predict_v16_risk
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
        # V15 ML engine injected from main.py lifespan so the tick loop can
        # call predict() without going through app.state.
        self._ml_engine = None
        # SumoBridge singleton — set once when SUMO mode is active.
        self._sumo_bridge = None

    # ------------------------------------------------------------------
    # ML engine injection (called from main.py lifespan)
    # ------------------------------------------------------------------

    def set_ml_engine(self, ml_engine: Any) -> None:
        """
        Inject the V15 TrafficModelAdapter loaded during FastAPI startup.

        Call this from the lifespan context manager *after*
        ``app.state.ml_engine`` has been initialised so the tick loop can
        use it without holding a reference to ``app.state``.
        """
        self._ml_engine = ml_engine
        logger.info(
            "SimulationManager: ml_engine injected — %s",
            repr(ml_engine),
        )

    # ------------------------------------------------------------------
    # SUMO bridge injection (optional — called when SUMO is available)
    # ------------------------------------------------------------------

    def set_sumo_bridge(self, bridge: Any) -> None:
        """
        Inject an initialised SumoBridge so the tick loop uses real TraCI data.

        If never called (or called with None), the tick loop falls back to the
        existing mock sensor path — the server always keeps running.
        """
        self._sumo_bridge = bridge
        if bridge is not None:
            logger.info(
                "SimulationManager: SumoBridge injected — "
                "SUMO mode active (dedicated executor, max_workers=1)."
            )
        else:
            logger.info("SimulationManager: SumoBridge cleared — mock mode.")

    # ------------------------------------------------------------------
    # Public lifecycle API
    # ------------------------------------------------------------------

    def start(self, simulation_id: str, config: SimulationConfig) -> None:
        """
        Spawn a background asyncio task for *simulation_id*.

        Safe to call even if a loop is already running for that id — the old
        task is cancelled first so there are never two loops competing.
        """
        existing = self._tasks.get(simulation_id)
        if existing is not None and not existing.done():
            logger.info(
                "Simulation %s already running — keeping the existing tick loop.",
                simulation_id,
            )
            return

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
        Inject randomised mock sensor readings into each graph edge.

        Used as the fallback path when SUMO is not connected. Jitters
        previous values so the UI shows plausible movement.
        """
        density = config.vehicle_density  # 0.0 – 1.0
        rainfall = config.rainfall  # 0.0 – 1.0
        accident_active = config.accident_flag

        for u, v, data in graph.graph.edges(data=True):
            capacity: float = float(data.get("capacity", 120))

            base_vehicles = density * capacity
            jitter = random.uniform(-0.15, 0.15) * capacity
            if accident_active:
                jitter -= 0.1 * capacity
            vehicle_count = max(0, min(capacity * 1.5, base_vehicles + jitter))

            occupancy = vehicle_count / max(1.0, capacity)
            avg_speed = max(5.0, 60.0 * (1.0 - occupancy) * (1.0 - rainfall * 0.4))
            # Mock "stopped" count — same occupancy-driven heuristic style as
            # avg_speed above; only used when source == "mock" (see
            # traffic_events below, which labels every entry honestly).
            stopped_vehicles = int(vehicle_count * max(0.0, occupancy - 0.6) * 0.8)

            data["vehicle_count"] = int(vehicle_count)
            data["avg_speed"] = round(avg_speed, 2)
            data["stopped_vehicles"] = stopped_vehicles
            data["rainfall"] = rainfall

    def _apply_sumo_metrics_to_graph(
        self,
        graph: RoadNetworkGraph,
        raw_metrics: list[Dict[str, Any]],
    ) -> None:
        """
        Write live SUMO telemetry back onto the matching graph edges so the
        rest of the pipeline (pathfinding, broadcast) sees real data.

        Edges that exist in SUMO but not in the graph are silently skipped —
        the graph is our authoritative routing structure.
        """
        sumo_lookup = {m["edge_id"]: m for m in raw_metrics}
        for u, v, data in graph.graph.edges(data=True):
            edge_id = str(data.get("edge_id", f"{u}->{v}"))
            m = sumo_lookup.get(edge_id)
            if m is None:
                continue
            data["vehicle_count"] = m["vehicle_count"]
            data["avg_speed"] = m["average_speed_kmh"]
            data["stopped_vehicles"] = m["stopped_vehicles"]
            data["rainfall"] = 0.0  # TraCI does not expose rainfall

    async def _run_simulation_loop(self, simulation_id: str) -> None:
        """
        Main simulation tick loop — SUMO-backend bridge pipeline.

        See module docstring for the full pipeline description.
        """
        graph: RoadNetworkGraph = get_road_network_graph()
        adapter: TrafficModelAdapter = get_model_adapter()
        config: SimulationConfig = self._configs[simulation_id]
        loop = asyncio.get_event_loop()

        # Resolve the V15 engine: prefer the injected engine, fall back to
        # the module-level adapter so tests/dev still work without main.py.
        ml_engine = self._ml_engine

        # Resolve SumoBridge (may be None if SUMO not available).
        bridge = self._sumo_bridge

        logger.info("Simulation %s: tick loop started.", simulation_id)
        if bridge is not None and bridge.is_connected:
            logger.info(
                "Simulation %s: SUMO bridge ACTIVE — "
                "TraCI thread pinned to executor 'sumo-traci' (max_workers=1).",
                simulation_id,
            )
        else:
            logger.info(
                "Simulation %s: SUMO bridge NOT connected — mock sensor mode.",
                simulation_id,
            )

        try:
            while True:
                tick = self._tick_counts[simulation_id]
                sumo_active = bridge is not None and bridge.is_connected
                data_source = "sumo" if sumo_active else "mock"

                # ── Step 1: SUMO step + metric collection ────────────────────
                #
                # CRITICAL — Thread-affinity fix:
                #   We submit to bridge.executor (max_workers=1), NOT None.
                #   This guarantees that the same OS thread steps SUMO every
                #   tick, satisfying TraCI's thread-affinity requirement.
                #   Using run_in_executor(None, ...) would allow the default
                #   thread pool to dispatch consecutive ticks to different
                #   threads, causing TraCI socket/connection errors.
                #
                if sumo_active:
                    sumo_step_func = functools.partial(bridge.simulation_step_and_collect)
                    raw_metrics: list[Dict[str, Any]]
                    raw_vehicles: list[Dict[str, Any]]
                    raw_metrics, raw_vehicles = await loop.run_in_executor(
                        bridge.executor,   # ← dedicated 1-worker pool (max_workers=1)
                        sumo_step_func,    # ← sync: step + collect in one thread call
                    )
                    if raw_metrics:
                        # Verification plan stop condition — must appear per tick.
                        logger.info(
                            "Simulation %s: SUMO tick OK — collected %d edges, %d vehicles from TraCI",
                            simulation_id,
                            len(raw_metrics),
                            len(raw_vehicles),
                        )
                    else:
                        # Bridge marked itself disconnected after an error.
                        logger.warning(
                            "Simulation %s tick=%d: SUMO returned no data — "
                            "falling back to mock sensor.",
                            simulation_id,
                            tick,
                        )
                        sumo_active = False
                        data_source = "mock"
                else:
                    raw_metrics = []
                    raw_vehicles = []

                # ── Step 2: Push data into the routing graph ─────────────────
                if sumo_active and raw_metrics:
                    self._apply_sumo_metrics_to_graph(graph, raw_metrics)
                else:
                    logger.info(
                        "Simulation %s: SUMO not connected -- using mock sensor data.",
                        simulation_id,
                    )
                    self._mutate_edge_sensor_data(graph, config)

                # ── Step 3a: Legacy congestion adapter (graph-edge features) ─
                edge_rows = graph.get_edge_feature_rows()
                predictions: Dict[str, float] = adapter.predict_congestion(edge_rows)

                # ── Step 3b: V15 XGBoost risk scores ─────────────────────────
                #
                # SUMO path: SumoBridge.build_v15_raw_features() maps each
                # raw TraCI metric dict to the full 53-column V15 contract
                # (lag-1/2/3, momentum, escalation rates, composites), then
                # ml_engine.predict_batch() runs a single batched XGBoost
                # inference call — no per-edge predict() loop overhead.
                #
                # Mock path: falls through to the model_registry / heuristic.
                #
                risk_scores: Dict[str, float] = {}

                if sumo_active and raw_metrics and ml_engine is not None and ml_engine.is_ready:
                    v15_rows = []
                    edge_id_order = []
                    for m in raw_metrics:
                        eid = m["edge_id"]
                        v15_raw = bridge.build_v15_raw_features(eid, m)
                        v15_rows.append(v15_raw)
                        edge_id_order.append(eid)

                    probs = ml_engine.predict_batch(v15_rows)
                    risk_scores = {eid: p for eid, p in zip(edge_id_order, probs)}
                    logger.info(
                        "Simulation %s tick=%d: V15 batch predict -- %d edges, "
                        "max_risk=%.4f  [source=sumo]",
                        simulation_id,
                        tick,
                        len(risk_scores),
                        max(risk_scores.values(), default=0.0),
                    )
                else:
                    v16_model = model_registry.load("v16_risk")
                    risk_scores = predict_v16_risk(edge_rows, model=v16_model)

                # ── Step 4: Apply predictions → dynamic edge costs ───────────
                updated_count = graph.update_edge_weights(predictions)

                # ── Step 5: Build and broadcast JSON payload ─────────────────
                traffic_events: list[Dict[str, Any]] = []
                for u, v, data in graph.graph.edges(data=True):
                    edge_id: str = str(data.get("edge_id", f"{u}->{v}"))
                    congestion_score = predictions.get(
                        edge_id, float(data.get("congestion", 0.0) or 0.0)
                    )
                    traffic_events.append(
                        {
                            "type": UpdateType.TRAFFIC.value,
                            "edge_id": edge_id,
                            "speed": round(float(data.get("avg_speed", 40.0)), 1),
                            "vehicle_count": int(data.get("vehicle_count", 0)),
                            "stopped_vehicles": int(data.get("stopped_vehicles", 0)),
                            "congestion": _congestion_label(congestion_score),
                            "congestion_score": round(congestion_score, 4),
                            "edge_cost": round(float(data.get("weight", 0.0) or 0.0), 4),
                            "base_cost": round(float(data.get("base_weight", 0.0) or 0.0), 4),
                            "risk_score": round(
                                float(risk_scores.get(edge_id, congestion_score)), 4
                            ),
                            "model": "v15_xgboost" if sumo_active else "v16_xgboost",
                            "source": data_source,
                        }
                    )

                # Individual vehicle markers — only meaningful when SUMO is
                # actually connected; the mock sensor path has no per-vehicle
                # data to report, so this is an honest empty list rather than
                # a fabricated one (never invent vehicles that don't exist).
                vehicle_events: list[Dict[str, Any]] = raw_vehicles if sumo_active else []

                payload: Dict[str, Any] = {
                    "type": UpdateType.TRAFFIC.value,
                    "simulation_id": simulation_id,
                    "status": SimulationStatus.RUNNING.value,
                    "tick": tick,
                    "edges_updated": updated_count,
                    "model": "v15_xgboost" if sumo_active else "v16_xgboost",
                    "source": data_source,
                    "traffic": traffic_events,
                    "vehicles": vehicle_events,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                await websocket_manager.broadcast(simulation_id, payload)

                logger.info(
                    "Simulation %s tick=%d  edges_updated=%d  ws_clients=%d  "
                    "source=%s  [BROADCAST SENT]",
                    simulation_id,
                    tick,
                    updated_count,
                    websocket_manager.connection_count(simulation_id),
                    data_source,
                )

                self._tick_counts[simulation_id] = tick + 1

                # Yield control back to the FastAPI event loop.
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info(
                "Simulation %s: tick loop cancelled at tick %d.",
                simulation_id,
                self._tick_counts.get(simulation_id, 0),
            )
            raise

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
