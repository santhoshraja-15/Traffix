"""
Ambulance service.

Bridges the API layer with AmbulanceManager and AmbulanceDispatcher.
"""
from __future__ import annotations

from typing import List, Optional

from app.emergency.ambulance_dispatcher import dispatch_ambulance
from app.emergency.ambulance_manager import AmbulanceRecord, ambulance_manager
from app.emergency.green_corridor import green_corridor
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AmbulanceService:
    """High-level ambulance operations for the API layer."""

    def list_units(self) -> List[AmbulanceRecord]:
        return ambulance_manager.all_units()

    def available_units(self) -> List[AmbulanceRecord]:
        return ambulance_manager.available_units()

    def dispatch(self, accident_id: str, accident_node: str) -> Optional[str]:
        """Dispatch the nearest ambulance to *accident_node* for *accident_id*."""
        return dispatch_ambulance(accident_id, accident_node)

    def update_position(self, ambulance_id: str, current_node: str, status: str) -> bool:
        unit = ambulance_manager.get(ambulance_id)
        if unit is None:
            return False
        ambulance_manager.update_status(ambulance_id, status, current_node)
        return True

    def complete_mission(self, ambulance_id: str) -> None:
        """Mark the ambulance as available again and deactivate its green corridor."""
        green_corridor.deactivate(ambulance_id)
        ambulance_manager.update_status(ambulance_id, "available")
        logger.info("AmbulanceService: ambulance %s mission complete.", ambulance_id)


# Module-level singleton.
_default_ambulance_service: Optional[AmbulanceService] = None


def get_ambulance_service() -> AmbulanceService:
    global _default_ambulance_service
    if _default_ambulance_service is None:
        _default_ambulance_service = AmbulanceService()
    return _default_ambulance_service
