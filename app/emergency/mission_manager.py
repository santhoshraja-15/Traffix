"""
Emergency mission state machine — the real 8-state ambulance dispatch
lifecycle from MASTER_PROMPT.md, driven entirely by the simulation's own
tick counter (never a frontend setTimeout/wall-clock timer):

  1. AMBULANCE_DISPATCHED   (nearest hospital + ambulance selected)
  2. GREEN_CORRIDOR_ACTIVE  (emergency route established)
  3. EN_ROUTE_TO_ACCIDENT   (position interpolated along the real outbound route)
  4. AMBULANCE_ARRIVED
  5. ON_SITE_RESPONSE       (holds for exactly ON_SITE_HOLD_TICKS ticks —
                             60, matching the sumocfg's 1s step-length, i.e.
                             genuinely 1 simulated minute, not a guess)
  6. RETURNING_TO_HOSPITAL  (a fresh route requested from the real routing
                             engine — may differ from the outbound route)
  7. EMERGENCY_COMPLETED    (held briefly for the UI, then the mission is
                             dropped and the accident is resolved for real)

Nearest hospital is chosen by real routing-engine travel time (never
straight-line distance) among real hospitals (app.integrations.
osm_poi_loader) that currently have an available ambulance. If no real
hospital data or no available ambulance exists, this honestly declines to
start a mission rather than fabricating one — see start_mission()'s
docstring.

Signal priority: no real TraCI traffic-light control exists anywhere in
this codebase (confirmed: no traci.trafficlight.* call in app/). Per
MASTER_PROMPT.md's instruction for exactly this situation, missions
report signal_priority_available=False rather than a faked
"signal active" state — the corridor is represented honestly as the
priority *route*, not a claimed traffic-light effect.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.emergency.ambulance_manager import AmbulanceRecord, ambulance_manager
from app.utils.geo import interpolate
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Matches scenarios/*/traffic.sumocfg's <step-length value="1"/> — one
# simulation tick really is one simulated second, so 60 ticks really is
# one simulated minute (see TECHNICAL_DEEP_DIVE.md on why this must be
# tick-driven, not a browser timer).
ON_SITE_HOLD_TICKS = 60
COMPLETED_DISPLAY_TICKS = 5  # how long a completed mission stays in the broadcast


class MissionState(str, Enum):
    AMBULANCE_DISPATCHED = "ambulance_dispatched"
    GREEN_CORRIDOR_ACTIVE = "green_corridor_active"
    EN_ROUTE_TO_ACCIDENT = "en_route_to_accident"
    AMBULANCE_ARRIVED = "ambulance_arrived"
    ON_SITE_RESPONSE = "on_site_response"
    RETURNING_TO_HOSPITAL = "returning_to_hospital"
    EMERGENCY_COMPLETED = "emergency_completed"


@dataclass
class RoutePlan:
    edges: List[str]
    coords: List[Tuple[float, float]]  # (lat, lng)
    travel_time_s: float


@dataclass
class EmergencyMission:
    mission_id: str
    accident_id: str
    edge_id: str
    hospital_id: str
    hospital_name: str
    ambulance_id: str
    unit_number: str
    state: MissionState
    state_since_tick: int
    dispatch_tick: int
    outbound: RoutePlan
    signal_priority_available: bool = False
    arrived_tick: Optional[int] = None
    on_site_until_tick: Optional[int] = None
    return_route: Optional[RoutePlan] = None
    departed_tick: Optional[int] = None
    completed_tick: Optional[int] = None
    # True once the current state has appeared in at least one broadcast —
    # used only by the two single-tick states (DISPATCHED, CORRIDOR_ACTIVE)
    # to guarantee each is actually observable for one real tick rather
    # than advancing before a client ever sees it. start_mission() runs
    # from an HTTP handler between tick loop iterations, so without this,
    # the tick() call that immediately follows would advance past a state
    # that was never included in any broadcast.
    state_broadcast_once: bool = False


def _interpolate_along_route(coords: List[Tuple[float, float]], fraction: float) -> Tuple[float, float]:
    """Position at *fraction* (0-1) of the way along *coords*, weighted by
    real segment length — not a naive index-based interpolation."""
    if not coords:
        return (0.0, 0.0)
    if len(coords) == 1 or fraction <= 0:
        return coords[0]
    if fraction >= 1:
        return coords[-1]

    from app.utils.geo import haversine_distance_m  # noqa: PLC0415

    seg_lengths = [
        haversine_distance_m(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
        for i in range(len(coords) - 1)
    ]
    total = sum(seg_lengths) or 1.0
    target = fraction * total

    covered = 0.0
    for i, seg_len in enumerate(seg_lengths):
        if covered + seg_len >= target or i == len(seg_lengths) - 1:
            seg_fraction = (target - covered) / seg_len if seg_len > 0 else 0.0
            return interpolate(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1], seg_fraction)
        covered += seg_len
    return coords[-1]


class MissionManager:
    """Owns all active emergency missions and advances them once per tick."""

    def __init__(self) -> None:
        self._missions: Dict[str, EmergencyMission] = {}
        self._by_accident: Dict[str, str] = {}

    def active_missions(self) -> List[EmergencyMission]:
        return list(self._missions.values())

    def get_by_accident(self, accident_id: str) -> Optional[EmergencyMission]:
        mission_id = self._by_accident.get(accident_id)
        return self._missions.get(mission_id) if mission_id else None

    def start_mission(self, accident_id: str, edge_id: str, current_tick: int) -> Optional[EmergencyMission]:
        """
        Dispatch the nearest available real ambulance (by real routing-
        engine travel time) to *edge_id*. Returns None — logging exactly
        why — rather than fabricating a mission, if there's no real
        hospital data, no available unit, or no real route between any
        hospital and the accident.
        """
        if accident_id in self._by_accident:
            return self._missions.get(self._by_accident[accident_id])

        from app.routing.graph_manager import get_road_network_graph  # noqa: PLC0415
        from app.services.routing_service import get_routing_service  # noqa: PLC0415

        ambulance_manager.ensure_seeded()
        graph = get_road_network_graph()
        routing = get_routing_service()

        endpoints = graph.get_edge_endpoints(edge_id)
        if endpoints is None:
            logger.warning("MissionManager: edge %s not in graph — cannot dispatch.", edge_id)
            return None
        accident_node, _ = endpoints

        available = ambulance_manager.available_units()
        if not available:
            logger.warning("MissionManager: no available ambulance units for accident %s.", accident_id)
            return None

        best_unit: Optional[AmbulanceRecord] = None
        best_route = None
        for unit in available:
            try:
                candidates = routing.get_candidate_routes(unit.current_node, accident_node, count=1)
            except Exception as exc:  # noqa: BLE001
                logger.debug("MissionManager: no route from %s to %s: %s", unit.current_node, accident_node, exc)
                continue
            if not candidates:
                continue
            candidate = candidates[0]
            if best_route is None or candidate.travel_time < best_route.travel_time:
                best_unit, best_route = unit, candidate

        if best_unit is None or best_route is None:
            logger.warning(
                "MissionManager: no real route found from any available ambulance to accident %s.",
                accident_id,
            )
            return None

        ambulance_manager.dispatch(best_unit.ambulance_id, accident_id)

        mission = EmergencyMission(
            mission_id=str(uuid.uuid4()),
            accident_id=accident_id,
            edge_id=edge_id,
            hospital_id=best_unit.hospital_id,
            hospital_name=best_unit.hospital_name,
            ambulance_id=best_unit.ambulance_id,
            unit_number=best_unit.unit_number,
            state=MissionState.AMBULANCE_DISPATCHED,
            state_since_tick=current_tick,
            dispatch_tick=current_tick,
            outbound=RoutePlan(
                edges=best_route.edges,
                coords=[(c.lat, c.lng) for c in best_route.coords],
                travel_time_s=max(best_route.travel_time, 1.0),
            ),
        )
        self._missions[mission.mission_id] = mission
        self._by_accident[accident_id] = mission.mission_id
        logger.info(
            "MissionManager: mission %s — %s dispatched from %s to accident %s (%.0fs ETA).",
            mission.mission_id, best_unit.unit_number, best_unit.hospital_name, accident_id,
            best_route.travel_time,
        )
        return mission

    def tick(self, current_tick: int) -> None:
        """Advance every active mission by one real simulation tick."""
        from app.services.accident_service import get_accident_service  # noqa: PLC0415
        from app.services.routing_service import get_routing_service  # noqa: PLC0415

        completed_ids: List[str] = []

        for mission in list(self._missions.values()):
            # These two states are held for exactly one real broadcast
            # before advancing (see EmergencyMission.state_broadcast_once).
            if mission.state == MissionState.AMBULANCE_DISPATCHED:
                if mission.state_broadcast_once:
                    mission.state = MissionState.GREEN_CORRIDOR_ACTIVE
                    mission.state_since_tick = current_tick
                    mission.state_broadcast_once = False
                else:
                    mission.state_broadcast_once = True

            elif mission.state == MissionState.GREEN_CORRIDOR_ACTIVE:
                if mission.state_broadcast_once:
                    mission.state = MissionState.EN_ROUTE_TO_ACCIDENT
                    mission.state_since_tick = current_tick
                else:
                    mission.state_broadcast_once = True

            elif mission.state == MissionState.EN_ROUTE_TO_ACCIDENT:
                elapsed = current_tick - mission.dispatch_tick
                if elapsed >= mission.outbound.travel_time_s:
                    mission.state = MissionState.AMBULANCE_ARRIVED
                    mission.state_since_tick = current_tick
                    mission.arrived_tick = current_tick
                    accident_node = mission.outbound.coords[-1] if mission.outbound.coords else None
                    if accident_node:
                        # snap the ambulance's graph position to the accident end of its route
                        endpoints = None
                        try:
                            from app.routing.graph_manager import get_road_network_graph  # noqa: PLC0415
                            endpoints = get_road_network_graph().get_edge_endpoints(mission.edge_id)
                        except Exception:  # noqa: BLE001
                            pass
                        if endpoints:
                            ambulance_manager.update_status(mission.ambulance_id, "at_scene", endpoints[0])

            elif mission.state == MissionState.AMBULANCE_ARRIVED:
                mission.state = MissionState.ON_SITE_RESPONSE
                mission.state_since_tick = current_tick
                mission.on_site_until_tick = current_tick + ON_SITE_HOLD_TICKS

            elif mission.state == MissionState.ON_SITE_RESPONSE:
                if mission.on_site_until_tick is not None and current_tick >= mission.on_site_until_tick:
                    # Compute the real return route now, from wherever the
                    # ambulance actually is — may genuinely differ from the
                    # outbound route if conditions have changed.
                    from app.routing.graph_manager import get_road_network_graph  # noqa: PLC0415
                    graph = get_road_network_graph()
                    routing = get_routing_service()
                    endpoints = graph.get_edge_endpoints(mission.edge_id)
                    unit = ambulance_manager.get(mission.ambulance_id)
                    return_route = None
                    if endpoints and unit:
                        accident_node = endpoints[0]
                        try:
                            candidates = routing.get_candidate_routes(accident_node, unit.home_node, count=1)
                            return_route = candidates[0] if candidates else None
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("MissionManager: return-route request failed: %s", exc)

                    if return_route is not None:
                        mission.return_route = RoutePlan(
                            edges=return_route.edges,
                            coords=[(c.lat, c.lng) for c in return_route.coords],
                            travel_time_s=max(return_route.travel_time, 1.0),
                        )
                        mission.state = MissionState.RETURNING_TO_HOSPITAL
                        mission.state_since_tick = current_tick
                        mission.departed_tick = current_tick
                        ambulance_manager.update_status(mission.ambulance_id, "returning")
                    else:
                        # No real return route available — complete the
                        # mission where it stands rather than getting stuck
                        # or inventing a path.
                        logger.warning(
                            "MissionManager: mission %s has no real return route — completing in place.",
                            mission.mission_id,
                        )
                        mission.state = MissionState.EMERGENCY_COMPLETED
                        mission.state_since_tick = current_tick
                        mission.completed_tick = current_tick
                        get_accident_service().resolve_accident(mission.accident_id)
                        ambulance_manager.update_status(mission.ambulance_id, "available", unit.home_node if unit else None)

            elif mission.state == MissionState.RETURNING_TO_HOSPITAL:
                if mission.return_route is not None:
                    elapsed = current_tick - (mission.departed_tick or current_tick)
                    if elapsed >= mission.return_route.travel_time_s:
                        mission.state = MissionState.EMERGENCY_COMPLETED
                        mission.state_since_tick = current_tick
                        mission.completed_tick = current_tick
                        get_accident_service().resolve_accident(mission.accident_id)
                        unit = ambulance_manager.get(mission.ambulance_id)
                        ambulance_manager.update_status(
                            mission.ambulance_id, "available", unit.home_node if unit else None
                        )
                        logger.info("MissionManager: mission %s completed.", mission.mission_id)

            elif mission.state == MissionState.EMERGENCY_COMPLETED:
                if current_tick - mission.state_since_tick >= COMPLETED_DISPLAY_TICKS:
                    completed_ids.append(mission.mission_id)

        for mission_id in completed_ids:
            mission = self._missions.pop(mission_id, None)
            if mission:
                self._by_accident.pop(mission.accident_id, None)

    def current_position(self, mission: EmergencyMission, current_tick: int) -> Tuple[float, float]:
        """Real interpolated (lat, lng) for *mission*'s ambulance right now —
        along the real outbound or return route, never an invented path."""
        if mission.state in (
            MissionState.AMBULANCE_DISPATCHED,
            MissionState.GREEN_CORRIDOR_ACTIVE,
            MissionState.EN_ROUTE_TO_ACCIDENT,
        ):
            elapsed = current_tick - mission.dispatch_tick
            fraction = elapsed / mission.outbound.travel_time_s
            return _interpolate_along_route(mission.outbound.coords, fraction)
        if mission.state in (MissionState.AMBULANCE_ARRIVED, MissionState.ON_SITE_RESPONSE):
            return mission.outbound.coords[-1] if mission.outbound.coords else (0.0, 0.0)
        if mission.state == MissionState.RETURNING_TO_HOSPITAL and mission.return_route is not None:
            elapsed = current_tick - (mission.departed_tick or current_tick)
            fraction = elapsed / mission.return_route.travel_time_s
            return _interpolate_along_route(mission.return_route.coords, fraction)
        if mission.state == MissionState.EMERGENCY_COMPLETED and mission.return_route is not None:
            return mission.return_route.coords[-1] if mission.return_route.coords else (0.0, 0.0)
        return mission.outbound.coords[0] if mission.outbound.coords else (0.0, 0.0)


# Module-level singleton.
mission_manager = MissionManager()
