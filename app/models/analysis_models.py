"""Metrics/analysis response schemas.

Shapes are derived directly from how ``app/api/analysis.py`` and
``app/services/analytics_service.py`` already construct and consume these
objects.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.utils.constants import SeverityLevel


class AIInsightMessage(BaseModel):
    insight_id: str
    severity: SeverityLevel
    title: str
    description: str
    recommendation: str
    estimated_delay: float  # seconds


class AnalysisResponse(BaseModel):
    insights: List[AIInsightMessage]
