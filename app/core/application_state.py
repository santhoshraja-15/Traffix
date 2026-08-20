"""
Application-wide state container.

Aggregates top-level runtime metadata (uptime, active simulation count, health
flags) that the /health endpoint and admin tools can query without wiring into
every subsystem directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ApplicationState:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active_simulations: int = 0
    total_simulations_started: int = 0
    websocket_clients: int = 0
    last_error: Optional[str] = None
    is_healthy: bool = True

    def record_simulation_start(self) -> None:
        self.active_simulations += 1
        self.total_simulations_started += 1

    def record_simulation_stop(self) -> None:
        self.active_simulations = max(0, self.active_simulations - 1)

    def uptime_seconds(self) -> float:
        delta = datetime.now(timezone.utc) - self.started_at
        return delta.total_seconds()


# Module-level singleton shared across the FastAPI process.
app_state = ApplicationState()
