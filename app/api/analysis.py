"""AI insight / analytics endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.models.analysis_models import AIInsightMessage, AnalysisResponse
from app.utils.constants import SeverityLevel

router = APIRouter(tags=["analysis"])


@router.get("/analysis/insights", response_model=AnalysisResponse)
async def get_insights() -> AnalysisResponse:
    insights = [
        AIInsightMessage(
            insight_id=str(uuid.uuid4()),
            severity=SeverityLevel.MEDIUM,
            title="Rising congestion on Anna Salai corridor",
            description="Vehicle density has increased 18% over the last 10 minutes.",
            recommendation="Consider signal retiming at 3 downstream intersections.",
            estimated_delay=95.0,
        ),
        AIInsightMessage(
            insight_id=str(uuid.uuid4()),
            severity=SeverityLevel.HIGH,
            title="Cascade risk detected near junction J-14",
            description="Queue spillback likely within 6 minutes if trend continues.",
            recommendation="Preemptively reroute 20% of inbound traffic.",
            estimated_delay=240.0,
        ),
    ]
    return AnalysisResponse(insights=insights)
