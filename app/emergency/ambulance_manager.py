"""
Ambulance fleet manager.

Tracks the positions and statuses of all registered ambulances. One
ambulance is seeded per real hospital (app.integrations.osm_poi_loader —
15 real hospitals/clinics in Anna Nagar, extracted from the project's own
OSM source data), each starting at the graph node nearest its real
hospital's real coordinates. This replaces the previous seeding at
synthetic mock-grid node IDs ("n0_0" etc.) that no longer exist on the
real network graph built in Phase 3.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AmbulanceRecord:
    ambulance_id: str
    unit_number: str
    current_node: str  # Graph node ID representing the ambulance's position
    hospital_id: str
    hospital_name: str
    home_node: str  # the node it returns to / redispatches from
    status: str = "available"  # "available" | "dispatched" | "at_scene" | "returning"
    assigned_accident_id: Optional[str] = None


class AmbulanceManager:
    """In-memory registry of ambulance units, seeded once real hospital data is available."""

    def __init__(self) -> None:
        self._fleet: Dict[str, AmbulanceRecord] = {}
        self._seeded = False

    def ensure_seeded(self) -> None:
        """
        Seed one ambulance per real hospital, snapped to the nearest real
        graph node. Idempotent — a no-op once seeded, and a no-op (not a
        crash) if the real network/hospital data isn't available yet, so
        callers can retry on a later tick once both have loaded.
        """
        if self._seeded:
            return

        from app.integrations.osm_poi_loader import get_real_hospitals  # noqa: PLC0415
        from app.routing.graph_manager import get_road_network_graph  # noqa: PLC0415

        hospitals = get_real_hospitals()
        graph = get_road_network_graph()
        if not hospitals or not graph.is_initialized:
            return

        for i, hospital in enumerate(hospitals):
            try:
                node_id, _dist_m = graph.get_nearest_node(hospital.lat, hospital.lng)
            except ValueError:
                continue
            aid = str(uuid.uuid4())
            self._fleet[aid] = AmbulanceRecord(
                ambulance_id=aid,
                unit_number=f"AMB-{i + 1:03d}",
                current_node=node_id,
                hospital_id=hospital.osm_id,
                hospital_name=hospital.name,
                home_node=node_id,
                status="available",
            )

        self._seeded = len(self._fleet) > 0
        if self._seeded:
            logger.info("AmbulanceManager: seeded %d units at real hospitals.", len(self._fleet))
        else:
            logger.warning("AmbulanceManager: no units seeded — no real hospital nodes resolved.")

    def available_units(self) -> List[AmbulanceRecord]:
        return [a for a in self._fleet.values() if a.status == "available"]

    def dispatch(self, ambulance_id: str, accident_id: str) -> bool:
        unit = self._fleet.get(ambulance_id)
        if unit is None or unit.status != "available":
            return False
        unit.status = "dispatched"
        unit.assigned_accident_id = accident_id
        logger.info("Ambulance %s dispatched to accident %s", unit.unit_number, accident_id)
        return True

    def update_status(self, ambulance_id: str, status: str, current_node: Optional[str] = None) -> None:
        unit = self._fleet.get(ambulance_id)
        if unit:
            unit.status = status
            if current_node:
                unit.current_node = current_node
            logger.debug("Ambulance %s status → %s", ambulance_id, status)

    def get(self, ambulance_id: str) -> Optional[AmbulanceRecord]:
        return self._fleet.get(ambulance_id)

    def all_units(self) -> List[AmbulanceRecord]:
        return list(self._fleet.values())


# Module-level singleton.
ambulance_manager = AmbulanceManager()
