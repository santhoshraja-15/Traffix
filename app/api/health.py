"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.utils.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
