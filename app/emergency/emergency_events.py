"""
Emergency domain events.

Defines typed event payloads published on the EventManager bus when
emergency-related state changes occur. Consumers (WebSocket broadcaster,
analytics) subscribe to these event names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

# Event name constants — import these to subscribe / publish.
ACCIDENT_REPORTED = "emergency.accident_reported"
ACCIDENT_RESOLVED = "emergency.accident_resolved"
AMBULANCE_DISPATCHED = "emergency.ambulance_dispatched"
GREEN_CORRIDOR_ACTIVATED = "emergency.green_corridor_activated"
GREEN_CORRIDOR_DEACTIVATED = "emergency.green_corridor_deactivated"


@dataclass
class AccidentReportedEvent:
    accident_id: str
    edge_id: str
    severity: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AmbulanceDispatchedEvent:
    ambulance_id: str
    accident_id: str
    origin_node: str
    destination_node: str
    dispatched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GreenCorridorEvent:
    ambulance_id: str
    corridor_path: Optional[List[str]]
    activated: bool  # True = activated, False = deactivated
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
