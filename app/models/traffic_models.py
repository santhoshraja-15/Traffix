"""Traffic/vehicle/edge schemas.

Shape derived directly from how ``app/api/traffic.py``'s
``GET /api/traffic/{edge_id}`` already constructs this object. Note the
WebSocket broadcast payload built by ``SimulationManager`` (the real, live
data path) uses its own plain-dict shape documented in
``FRONTEND_AUDIT.md`` §1.2 — it does not go through this model.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.utils.constants import CongestionLevel, UpdateType


class TrafficUpdate(BaseModel):
    type: UpdateType
    edge_id: str
    speed: float
    vehicle_count: int
    congestion: CongestionLevel
