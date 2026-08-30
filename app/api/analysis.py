"""AI insight / analytics endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.analysis_models import AnalysisResponse
from app.services.analytics_service import get_analytics_service

router = APIRouter(tags=["analysis"])


@router.get("/analysis/insights", response_model=AnalysisResponse)
async def get_insights() -> AnalysisResponse:
    """
    Real AI insight messages derived from the live traffic_state_store (see
    app/services/analytics_service.py) — the most congested/highest-risk
    edges right now, with a real recommendation and a real estimated delay
    computed from that edge's actual congestion score. Previously this
    endpoint ignored the (already-real) analytics service entirely and
    returned two hardcoded insights naming roads that don't even exist in
    the real Anna Nagar network ("Anna Salai corridor", "junction J-14").
    """
    insights = get_analytics_service().generate_insights()
    return AnalysisResponse(insights=insights)
