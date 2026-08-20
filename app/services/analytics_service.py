"""
Analytics service.

Generates AI-style insights from live traffic state and simulation data.
Used by the /analysis API endpoint to serve AIInsightMessage payloads.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from app.core.traffic_state import traffic_state_store
from app.models.analysis_models import AIInsightMessage
from app.utils.constants import CongestionLevel, SeverityLevel
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _severity_for_congestion(level: CongestionLevel) -> SeverityLevel:
    return {
        CongestionLevel.FREE_FLOW: SeverityLevel.INFO,
        CongestionLevel.LIGHT: SeverityLevel.LOW,
        CongestionLevel.MODERATE: SeverityLevel.MEDIUM,
        CongestionLevel.HEAVY: SeverityLevel.HIGH,
        CongestionLevel.SEVERE: SeverityLevel.CRITICAL,
    }.get(level, SeverityLevel.INFO)


class AnalyticsService:
    """Derives AI insight messages from current traffic state."""

    def generate_insights(self, max_insights: int = 5) -> List[AIInsightMessage]:
        """
        Scan the live edge states and produce insight messages for the
        most congested / highest-risk edges.
        """
        states = sorted(
            traffic_state_store.all_states().values(),
            key=lambda s: s.congestion_score,
            reverse=True,
        )[:max_insights]

        if not states:
            # Return a placeholder insight when no simulation is running.
            return [
                AIInsightMessage(
                    insight_id=str(uuid.uuid4()),
                    severity=SeverityLevel.INFO,
                    title="System Nominal",
                    description="No active simulation data. Start a simulation to generate insights.",
                    recommendation="Use POST /api/simulation/start to begin a scenario.",
                    estimated_delay=0.0,
                )
            ]

        insights: List[AIInsightMessage] = []
        for state in states:
            cong_pct = int(state.congestion_score * 100)
            severity = _severity_for_congestion(state.congestion_level)
            delay_s = state.congestion_score * 300  # rough delay: up to 5 min

            insights.append(
                AIInsightMessage(
                    insight_id=str(uuid.uuid4()),
                    severity=severity,
                    title=f"High congestion on edge {state.edge_id}",
                    description=(
                        f"Edge {state.edge_id} is at {cong_pct}% congestion "
                        f"({state.congestion_level.value}). "
                        f"Current speed: {state.speed:.1f} km/h with "
                        f"{state.vehicle_count} vehicles."
                    ),
                    recommendation=(
                        "Consider rerouting traffic via alternative edges or "
                        "adjusting signal timing to reduce queue length."
                    ),
                    estimated_delay=round(delay_s, 1),
                )
            )
        return insights


# Module-level singleton.
_default_analytics: AnalyticsService | None = None


def get_analytics_service() -> AnalyticsService:
    global _default_analytics
    if _default_analytics is None:
        _default_analytics = AnalyticsService()
    return _default_analytics
