"""
Accident service.

Bridges the API layer with AccidentManager and EmergencyRouting,
so accident endpoints never import emergency internals directly.
"""
from __future__ import annotations

from typing import List, Optional

from app.emergency.accident_manager import AccidentRecord, accident_manager
from app.emergency.emergency_routing import handle_accident
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AccidentService:
    """High-level accident operations for the API layer."""

    def report_accident(
        self,
        edge_id: str,
        severity: str = "moderate",
        location_description: str = "",
    ) -> dict:
        """
        Report a new accident and trigger the emergency response pipeline.

        Returns a response dict suitable for direct serialisation.
        """
        logger.info("AccidentService.report_accident: edge=%s severity=%s", edge_id, severity)
        return handle_accident(edge_id, severity, location_description)

    def resolve_accident(self, accident_id: str) -> bool:
        """Mark *accident_id* as resolved."""
        return accident_manager.resolve(accident_id)

    def active_accidents(self) -> List[AccidentRecord]:
        return accident_manager.active_accidents()

    def get_accident(self, accident_id: str) -> Optional[AccidentRecord]:
        return accident_manager.get(accident_id)


# Module-level singleton.
_default_accident_service: Optional[AccidentService] = None


def get_accident_service() -> AccidentService:
    global _default_accident_service
    if _default_accident_service is None:
        _default_accident_service = AccidentService()
    return _default_accident_service
