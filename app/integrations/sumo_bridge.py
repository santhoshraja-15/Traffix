"""
SUMO-Backend Bridge
===================

Wraps the synchronous SUMO/TraCI interaction into a FastAPI-safe module.

Thread-Affinity Design
----------------------
TraCI is single-threaded and expects all calls to originate from the OS thread
that originally connected to SUMO.  Running ``traci.simulationStep()`` through
Python's *default* thread pool (``run_in_executor(None, ...)``) is dangerous
because the pool may dispatch consecutive ticks to different threads, causing
socket/connection errors.

Mitigation: ``SumoBridge`` owns a **dedicated**
``concurrent.futures.ThreadPoolExecutor(max_workers=1)``.  All TraCI calls are
submitted exclusively to this single-worker pool, guaranteeing that the same
OS thread handles every tick for the lifetime of the bridge.

Usage (inside an async function)
---------------------------------
::

    bridge = SumoBridge()
    bridge.connect()

    loop = asyncio.get_event_loop()
    raw_metrics = await loop.run_in_executor(
        bridge.executor,                      # dedicated 1-worker pool
        bridge.simulation_step_and_collect,   # sync: step + collect in one call
    )

    for m in raw_metrics:
        v15_row = bridge.build_v15_raw_features(m["edge_id"], m)
        risk = ml_engine.predict(v15_row)

    bridge.shutdown()   # call on app teardown
"""
from __future__ import annotations

import collections
import math
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Deque, Dict, List, Optional, Tuple

from app.integrations.sumo_network_loader import get_real_network
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# TraCI availability guard
# ---------------------------------------------------------------------------
try:
    import traci  # type: ignore[import]
    SUMO_AVAILABLE: bool = True
except ImportError:
    traci = None  # type: ignore[assignment]
    SUMO_AVAILABLE = False
    logger.warning(
        "SumoBridge: 'traci' not found -- running in MOCK mode. "
        "Install SUMO and add it to PATH to enable live data."
    )

# Vehicle is considered stopped below this speed (m/s)
_STOP_SPEED_MS: float = 5.0 / 3.6
# Approximate vehicle body length for queue estimation (metres)
_AVG_VEHICLE_LEN_M: float = 5.0
# How many historical snapshots to keep per edge (for lag-2 / lag-3 features)
_HISTORY_DEPTH: int = 4


# ---------------------------------------------------------------------------
# Per-edge snapshot (one tick worth of raw TraCI data)
# ---------------------------------------------------------------------------

class _EdgeSnapshot:
    """One tick of raw data for a single road edge."""
    __slots__ = (
        "vehicle_count",
        "average_speed_kmh",
        "stopped_vehicles",
        "average_waiting_time",
        "density_veh_per_km",
        "queue_length_estimate_m",
        "road_length_m",
    )

    def __init__(
        self,
        vehicle_count: int = 0,
        average_speed_kmh: float = 0.0,
        stopped_vehicles: int = 0,
        average_waiting_time: float = 0.0,
        density_veh_per_km: float = 0.0,
        queue_length_estimate_m: float = 0.0,
        road_length_m: float = 0.0,
    ) -> None:
        self.vehicle_count = vehicle_count
        self.average_speed_kmh = average_speed_kmh
        self.stopped_vehicles = stopped_vehicles
        self.average_waiting_time = average_waiting_time
        self.density_veh_per_km = density_veh_per_km
        self.queue_length_estimate_m = queue_length_estimate_m
        self.road_length_m = road_length_m


# ---------------------------------------------------------------------------
# SumoBridge
# ---------------------------------------------------------------------------

class SumoBridge:
    """
    Manages SUMO/TraCI interaction for the async simulation tick loop.

    All synchronous TraCI calls are funnelled through a single-worker
    ThreadPoolExecutor to avoid TraCI thread-affinity requirement.
    """

    def __init__(self) -> None:
        # Thread-affinity fix: ONE worker thread, lives for the life of the
        # bridge.  Submit every TraCI call to this executor -- never to the
        # default pool (run_in_executor(None, ...)).
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="sumo-traci",
        )

        self._connected: bool = False
        self._road_edges: List[str] = []
        self._road_lengths: Dict[str, float] = {}

        # Per-edge ring buffer: deque of _EdgeSnapshot (newest at right).
        self._history: Dict[str, Deque[_EdgeSnapshot]] = {}

        # Real network object (app.integrations.sumo_network_loader), used to
        # convert live vehicle positions from SUMO's internal x/y to lon/lat
        # with the exact same projection the static topology graph uses —
        # never a second, independently-guessed conversion.
        self._net: Optional[Any] = None

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def executor(self) -> ThreadPoolExecutor:
        """The dedicated 1-worker executor. Pass this to run_in_executor()."""
        return self._executor

    @property
    def is_connected(self) -> bool:
        return self._connected and SUMO_AVAILABLE

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """
        Start the SUMO process headlessly and connect via TraCI.
        Returns True on success, False if unavailable (bridge uses mock data).
        """
        if not SUMO_AVAILABLE:
            logger.warning("SumoBridge.connect: TraCI not available -- mock mode.")
            return False

        try:
            # Thread-affinity fix requires starting it within the OS process,
            # but wait, traci.start spawns it and connects this OS thread.
            import os
            # Ensure SUMO_HOME is set or rely on PATH
            sumo_cmd = ["sumo", "-c", "scenarios/medium/traffic.sumocfg"]
            try:
                # If a traci connection is already open, this will throw an error, 
                # so we can catch it or close it, but starting fresh is safer.
                traci.start(sumo_cmd)
            except Exception as e:
                # If already started
                logger.warning(f"traci.start threw an error, trying to proceed: {e}")

            all_edges: List[str] = traci.edge.getIDList()
            self._road_edges = [e for e in all_edges if not e.startswith(":")]

            for road_id in self._road_edges:
                try:
                    n_lanes = traci.edge.getLaneNumber(road_id)
                    if n_lanes > 0:
                        self._road_lengths[road_id] = traci.lane.getLength(f"{road_id}_0")
                    else:
                        self._road_lengths[road_id] = 0.0
                except Exception:
                    self._road_lengths[road_id] = 0.0
                self._history[road_id] = collections.deque(maxlen=_HISTORY_DEPTH)

            real_network = get_real_network()
            self._net = real_network.net if real_network is not None else None
            if self._net is None:
                logger.warning(
                    "SumoBridge.connect: real network unavailable — live vehicle "
                    "positions cannot be converted to lon/lat and will be omitted "
                    "from the broadcast until it loads."
                )

            self._connected = True
            logger.info(
                "SumoBridge connected -- %d road edges discovered.",
                len(self._road_edges),
            )
            return True

        except Exception as exc:
            logger.error("SumoBridge.connect failed: %s", exc)
            self._connected = False
            return False

    def shutdown(self) -> None:
        """
        Cleanly shut down the dedicated executor.
        Call from the FastAPI lifespan shutdown block.
        """
        logger.info("SumoBridge: shutting down executor (wait=True) ...")
        self._executor.shutdown(wait=True)
        self._connected = False
        logger.info("SumoBridge: executor shutdown complete.")

    # ------------------------------------------------------------------
    # The single sync callable submitted to the dedicated executor
    # ------------------------------------------------------------------

    def simulation_step_and_collect(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        SYNCHRONOUS -- designed to run inside run_in_executor(bridge.executor, ...).

        1. Advances SUMO by one step via traci.simulationStep().
        2. Reads per-edge vehicle metrics (road_collector_v2 algorithm) AND
           per-vehicle position/heading in the same pass over
           traci.vehicle.getIDList() (one iteration, not two).
        3. Updates the per-edge history ring buffer.
        4. Returns (edge_metrics, vehicles) — edge_metrics ready for V15
           feature engineering, vehicles ready to broadcast for live map
           markers (empty if the real network's projection isn't available,
           since positions can't be honestly converted to lon/lat then).

        Returns ([], []) if SUMO is not connected (caller falls back to mock).
        """
        if not self._connected or not SUMO_AVAILABLE:
            return [], []

        try:
            # Step 1: Advance SUMO
            traci.simulationStep()

            # Step 2: Initialise per-road accumulators
            roads: Dict[str, Dict[str, Any]] = {
                road_id: {
                    "vehicle_count": 0,
                    "total_speed": 0.0,
                    "total_waiting": 0.0,
                    "stopped_vehicles": 0,
                }
                for road_id in self._road_edges
            }

            # Step 3: Accumulate vehicle telemetry + collect live positions
            vehicles: List[Dict[str, Any]] = []
            for vid in traci.vehicle.getIDList():
                road_id = traci.vehicle.getRoadID(vid)
                speed = traci.vehicle.getSpeed(vid)

                if self._net is not None:
                    x, y = traci.vehicle.getPosition(vid)
                    try:
                        lng, lat = self._net.convertXY2LonLat(x, y)
                        vehicles.append({
                            "id": vid,
                            "lat": lat,
                            "lng": lng,
                            # SUMO's vehicle angle is already compass-bearing
                            # convention (0 = north, clockwise) — no conversion needed.
                            "heading": traci.vehicle.getAngle(vid),
                            "speed_kmh": round(speed * 3.6, 2),
                            "edge_id": road_id,
                        })
                    except Exception:  # noqa: BLE001
                        pass  # skip this vehicle's marker rather than broadcast a bad position

                if road_id.startswith(":") or road_id not in roads:
                    continue
                waiting = traci.vehicle.getWaitingTime(vid)
                roads[road_id]["vehicle_count"] += 1
                roads[road_id]["total_speed"] += speed
                roads[road_id]["total_waiting"] += waiting
                if speed < _STOP_SPEED_MS:
                    roads[road_id]["stopped_vehicles"] += 1

            # Step 4: Compute derived metrics + update history
            results: List[Dict[str, Any]] = []
            for road_id in self._road_edges:
                acc = roads[road_id]
                vehicle_count: int = acc["vehicle_count"]
                road_length: float = self._road_lengths.get(road_id, 0.0)

                if vehicle_count > 0:
                    avg_speed_kmh = (acc["total_speed"] / vehicle_count) * 3.6
                    avg_waiting = acc["total_waiting"] / vehicle_count
                else:
                    avg_speed_kmh = 0.0
                    avg_waiting = 0.0

                density = (vehicle_count / (road_length / 1000.0)) if road_length > 0 else 0.0
                queue_m = acc["stopped_vehicles"] * _AVG_VEHICLE_LEN_M

                snap = _EdgeSnapshot(
                    vehicle_count=vehicle_count,
                    average_speed_kmh=round(avg_speed_kmh, 3),
                    stopped_vehicles=acc["stopped_vehicles"],
                    average_waiting_time=round(avg_waiting, 3),
                    density_veh_per_km=round(density, 3),
                    queue_length_estimate_m=round(queue_m, 3),
                    road_length_m=round(road_length, 3),
                )
                self._history[road_id].append(snap)

                results.append({
                    "edge_id": road_id,
                    "road_length_m": snap.road_length_m,
                    "vehicle_count": snap.vehicle_count,
                    "average_speed_kmh": snap.average_speed_kmh,
                    "stopped_vehicles": snap.stopped_vehicles,
                    "average_waiting_time": snap.average_waiting_time,
                    "density_veh_per_km": snap.density_veh_per_km,
                    "queue_length_estimate_m": snap.queue_length_estimate_m,
                })

            logger.info(
                "SumoBridge: SUMO tick OK -- collected %d edges, %d vehicle positions from TraCI.",
                len(results),
                len(vehicles),
            )
            return results, vehicles

        except Exception as exc:
            logger.error(
                "SumoBridge.simulation_step_and_collect error: %s", exc, exc_info=True
            )
            self._connected = False  # Mark disconnected so caller falls back to mock
            return [], []

    # ------------------------------------------------------------------
    # V15 Feature Engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_div(a: float, b: float) -> float:
        """Division returning 0.0 on zero-denominator, inf, or NaN."""
        if b == 0.0 or math.isnan(b) or math.isinf(b):
            return 0.0
        result = a / b
        return 0.0 if math.isnan(result) or math.isinf(result) else result

    def build_v15_raw_features(
        self,
        edge_id: str,
        current: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the full 53-column V15 feature dict for a single edge.

        Parameters
        ----------
        edge_id : str
            SUMO road edge identifier.
        current : Dict
            Raw metric dict from simulation_step_and_collect for this tick.

        Returns
        -------
        Dict[str, Any]
            All 53 V15 features. Missing history defaults to 0.0.
        """
        hist = list(self._history.get(edge_id, []))  # oldest -> newest

        # Current-tick values
        vc   = float(current.get("vehicle_count", 0))
        spd  = float(current.get("average_speed_kmh", 0.0))
        stop = float(current.get("stopped_vehicles", 0))
        wait = float(current.get("average_waiting_time", 0.0))
        dens = float(current.get("density_veh_per_km", 0.0))
        qlen = float(current.get("queue_length_estimate_m", 0.0))
        rlen = float(current.get("road_length_m", 0.0))
        vp100 = self._safe_div(vc, rlen / 100.0) if rlen > 0 else 0.0
        qrat  = self._safe_div(qlen, rlen) if rlen > 0 else 0.0

        # Lag-1 (previous tick)
        lag1 = hist[-2] if len(hist) >= 2 else None
        prev_spd  = lag1.average_speed_kmh         if lag1 else spd
        prev_vc   = float(lag1.vehicle_count)      if lag1 else vc
        prev_dens = lag1.density_veh_per_km        if lag1 else dens
        prev_qlen = lag1.queue_length_estimate_m   if lag1 else qlen
        prev_stop = float(lag1.stopped_vehicles)   if lag1 else stop

        spd_chg      = spd  - prev_spd
        vc_chg       = vc   - prev_vc
        dens_chg     = dens - prev_dens
        qlen_chg     = qlen - prev_qlen
        spd_chg_pct  = self._safe_div(spd_chg, prev_spd)
        vc_chg_pct   = self._safe_div(vc_chg,  prev_vc)

        # Lag-2
        lag2 = hist[-3] if len(hist) >= 3 else None
        spd_lag2  = lag2.average_speed_kmh         if lag2 else prev_spd
        vc_lag2   = float(lag2.vehicle_count)      if lag2 else prev_vc
        dens_lag2 = lag2.density_veh_per_km        if lag2 else prev_dens
        q_lag2    = lag2.queue_length_estimate_m   if lag2 else prev_qlen
        stop_lag2 = float(lag2.stopped_vehicles)   if lag2 else prev_stop

        # Lag-3
        lag3 = hist[-4] if len(hist) >= 4 else None
        spd_lag3  = lag3.average_speed_kmh         if lag3 else spd_lag2
        vc_lag3   = float(lag3.vehicle_count)      if lag3 else vc_lag2
        dens_lag3 = lag3.density_veh_per_km        if lag3 else dens_lag2
        q_lag3    = lag3.queue_length_estimate_m   if lag3 else q_lag2
        stop_lag3 = float(lag3.stopped_vehicles)   if lag3 else stop_lag2

        # 2-step momentum
        spd_chg2  = spd  - spd_lag2
        vc_chg2   = vc   - vc_lag2
        dens_chg2 = dens - dens_lag2
        q_chg2    = qlen - q_lag2
        stop_chg2 = stop - stop_lag2

        # 3-step momentum
        spd_chg3  = spd  - spd_lag3
        vc_chg3   = vc   - vc_lag3
        dens_chg3 = dens - dens_lag3
        q_chg3    = qlen - q_lag3
        stop_chg3 = stop - stop_lag3

        # Risk escalation rates
        spd_red_rate = self._safe_div(-spd_chg,  max(prev_spd, 0.001))
        dens_grow    = self._safe_div(dens_chg,  max(prev_dens, 0.001))
        q_grow       = self._safe_div(qlen_chg,  max(prev_qlen, 0.001))
        vc_grow      = self._safe_div(vc_chg,    max(prev_vc,   0.001))
        stop_chg_val = stop - prev_stop
        stop_grow    = self._safe_div(stop_chg_val, max(prev_stop, 0.001))

        # Second-order / acceleration (change-in-change)
        lag1_spd_chg  = (prev_spd  - spd_lag2) if lag2 else 0.0
        lag1_vc_chg   = (prev_vc   - vc_lag2)  if lag2 else 0.0
        lag1_dens_chg = (prev_dens - dens_lag2) if lag2 else 0.0
        lag1_q_chg    = (prev_qlen - q_lag2)    if lag2 else 0.0
        lag1_stop_chg = (prev_stop - stop_lag2) if lag2 else 0.0

        spd_acc  = spd_chg  - lag1_spd_chg
        vc_acc   = vc_chg   - lag1_vc_chg
        dens_acc = dens_chg - lag1_dens_chg
        q_acc    = qlen_chg - lag1_q_chg
        stop_acc = stop_chg_val - lag1_stop_chg

        # Composite / interaction
        traffic_pressure   = dens * max(0.0, 1.0 - self._safe_div(spd, 60.0))
        q_dens_pressure    = qlen * dens
        spd_dens_ratio     = self._safe_div(spd, max(dens, 0.001))
        escalation_score   = (
            0.4 * max(0.0, -spd_chg / max(prev_spd, 1.0))
            + 0.3 * max(0.0, dens_grow)
            + 0.3 * max(0.0, q_grow)
        )

        return {
            # Base (19)
            "vehicle_count":           vc,
            "average_speed_kmh":       spd,
            "stopped_vehicles":        stop,
            "average_waiting_time":    wait,
            "density_veh_per_km":      dens,
            "queue_length_estimate_m": qlen,
            "road_length_m":           rlen,
            "vehicles_per_100m":       vp100,
            "queue_ratio":             qrat,
            "previous_speed_kmh":      prev_spd,
            "previous_vehicle_count":  prev_vc,
            "previous_density":        prev_dens,
            "previous_queue_length_m": prev_qlen,
            "speed_change_kmh":        spd_chg,
            "vehicle_change":          vc_chg,
            "density_change":          dens_chg,
            "queue_change_m":          qlen_chg,
            "speed_change_pct":        spd_chg_pct,
            "vehicle_change_pct":      vc_chg_pct,
            # Lag-2 (5)
            "speed_lag2":              spd_lag2,
            "vehicle_lag2":            vc_lag2,
            "density_lag2":            dens_lag2,
            "queue_lag2":              q_lag2,
            "stopped_lag2":            stop_lag2,
            # Lag-3 (5)
            "speed_lag3":              spd_lag3,
            "vehicle_lag3":            vc_lag3,
            "density_lag3":            dens_lag3,
            "queue_lag3":              q_lag3,
            "stopped_lag3":            stop_lag3,
            # 2-step momentum (5)
            "speed_change_2step":      spd_chg2,
            "vehicle_change_2step":    vc_chg2,
            "density_change_2step":    dens_chg2,
            "queue_change_2step":      q_chg2,
            "stopped_change_2step":    stop_chg2,
            # 3-step momentum (5)
            "speed_change_3step":      spd_chg3,
            "vehicle_change_3step":    vc_chg3,
            "density_change_3step":    dens_chg3,
            "queue_change_3step":      q_chg3,
            "stopped_change_3step":    stop_chg3,
            # Risk escalation rates (5)
            "speed_reduction_rate":    spd_red_rate,
            "density_growth_rate":     dens_grow,
            "queue_growth_rate":       q_grow,
            "vehicle_growth_rate":     vc_grow,
            "stopped_growth_rate":     stop_grow,
            # Second-order / acceleration (5)
            "speed_acceleration":      spd_acc,
            "density_acceleration":    dens_acc,
            "queue_acceleration":      q_acc,
            "vehicle_acceleration":    vc_acc,
            "stopped_acceleration":    stop_acc,
            # Composite / interaction (4)
            "traffic_pressure":        traffic_pressure,
            "queue_density_pressure":  q_dens_pressure,
            "speed_density_ratio":     spd_dens_ratio,
            "escalation_score":        escalation_score,
        }
