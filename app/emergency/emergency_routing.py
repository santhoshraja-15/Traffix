"""
Emergency routing orchestrator.

Ties together AmbulanceDispatcher, GreenCorridor, and AccidentManager to
coordinate the full emergency response:
  1. Report accident → AccidentManager
  2. Dispatch nearest ambulance → AmbulanceDispatcher
  3. Activate green corridor along the emergency route → GreenCorridor
"""
from __future__ import annotations

from typing import Optional

from app.emergency.accident_manager import accident_manager
from app.emergency.ambulance_dispatcher import dispatch_ambulance
from app.emergency.ambulance_manager import ambulance_manager
from app.emergency.green_corridor import green_corridor
from app.utils.logging import get_logger

logger = get_logger(__name__)


def handle_accident(
    edge_id: str,
    severity: str = "moderate",
    location_description: str = "",
) -> dict:
    """
    Full emergency response pipeline for a new accident.

    Returns a summary dict suitable for direct use as an API response payload.
    """
    # 1. Record accident.
    record = accident_manager.report(edge_id, severity, location_description)

    # 2. Determine the accident node (use the source end of the edge).
    accident_node = edge_id.split("->")[0] if "->" in edge_id else "n0_0"

    # 3. Dispatch the nearest ambulance.
    ambulance_id = dispatch_ambulance(record.accident_id, accident_node)

    # 4. Activate green corridor if we have an ambulance.
    corridor_path: Optional[list] = None
    if ambulance_id:
        unit = ambulance_manager.get(ambulance_id)
        if unit:
            corridor_path = green_corridor.activate(
                ambulance_id,
                origin_node=unit.current_node,
                destination_node=accident_node,
            )

    return {
        "accident_id": record.accident_id,
        "edge_id": edge_id,
        "severity": severity,
        "ambulance_id": ambulance_id,
        "green_corridor_path": corridor_path,
        "status": "dispatched" if ambulance_id else "no_unit_available",
    }
