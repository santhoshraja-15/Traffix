"""Shared Pydantic field validators."""
from __future__ import annotations


def is_valid_lat(lat: float) -> bool:
    return -90.0 <= lat <= 90.0


def is_valid_lng(lng: float) -> bool:
    return -180.0 <= lng <= 180.0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
