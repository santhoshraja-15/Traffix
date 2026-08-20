"""
Ambulance fleet manager.

Tracks the positions and statuses of all registered ambulances.
The dispatcher consults this to select the optimal unit for dispatch.
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
    status: str = "available"  # "available" | "dispatched" | "at_scene" | "returning"
    assigned_accident_id: Optional[str] = None


class AmbulanceManager:
    """In-memory registry of ambulance units."""

    def __init__(self) -> None:
        self._fleet: Dict[str, AmbulanceRecord] = {}
        # Seed a few mock ambulances for the demo.
        self._seed_fleet()

    def _seed_fleet(self) -> None:
        for i, node in enumerate(["n0_0", "n2_3", "n5_5"]):
            aid = str(uuid.uuid4())
            self._fleet[aid] = AmbulanceRecord(
                ambulance_id=aid,
                unit_number=f"AMB-{i + 1:03d}",
                current_node=node,
                status="available",
            )

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
