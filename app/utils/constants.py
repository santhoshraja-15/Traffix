"""Shared enums and constant values used across the app."""
from __future__ import annotations

from enum import Enum


class TravelMode(str, Enum):
    DRIVING = "driving"
    EMERGENCY = "emergency"
    WALKING = "walking"


class CongestionLevel(str, Enum):
    FREE_FLOW = "free_flow"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    SEVERE = "severe"


class SeverityLevel(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScenarioType(str, Enum):
    ACCIDENT = "accident"
    ROAD_BLOCK = "road_block"
    DEMAND_SPIKE = "demand_spike"
    RAINFALL = "rainfall"
    SIGNAL_RETIMING = "signal_retiming"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class UpdateType(str, Enum):
    TRAFFIC = "traffic"
    ACCIDENT = "accident"
    AMBULANCE = "ambulance"
    SIGNAL = "signal"
    VEHICLE_POSITION = "vehicle_position"


DEFAULT_SRID = 4326  # WGS84, matches frontend Mapbox/deck.gl coordinate system
EARTH_RADIUS_METERS = 6_371_000
