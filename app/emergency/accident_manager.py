"""
Accident lifecycle manager.

Tracks active accident records in memory and exposes methods to create,
resolve, and query them. The emergency routing layer subscribes to accident
events to trigger green-corridor setup and rerouting.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AccidentRecord:
    accident_id: str
    edge_id: str
    severity: str  # "minor" | "moderate" | "critical"
    location_description: str = ""
    reported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.resolved_at is None


class AccidentManager:
    """In-memory store for accident records."""

    def __init__(self) -> None:
        self._records: Dict[str, AccidentRecord] = {}

    def report(
        self,
        edge_id: str,
        severity: str = "moderate",
        location_description: str = "",
    ) -> AccidentRecord:
        """Create and store a new accident record; return it."""
        record = AccidentRecord(
            accident_id=str(uuid.uuid4()),
            edge_id=edge_id,
            severity=severity,
            location_description=location_description,
        )
        self._records[record.accident_id] = record
        logger.info("Accident reported: %s on edge %s (severity=%s)", record.accident_id, edge_id, severity)
        return record

    def resolve(self, accident_id: str) -> bool:
        """Mark an accident as resolved. Returns True if found."""
        record = self._records.get(accident_id)
        if record is None:
            return False
        record.resolved_at = datetime.now(timezone.utc)
        logger.info("Accident resolved: %s", accident_id)
        return True

    def active_accidents(self) -> List[AccidentRecord]:
        return [r for r in self._records.values() if r.is_active]

    def get(self, accident_id: str) -> Optional[AccidentRecord]:
        return self._records.get(accident_id)


# Module-level singleton.
accident_manager = AccidentManager()
