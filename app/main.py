"""
TRAFFICX API entry point.

Run with:
    uvicorn app.main:app --reload

The ``lifespan`` context manager replaces the deprecated ``@app.on_event``
approach. On startup it logs the server boot. On shutdown it calls
``simulation_manager.stop_all()`` to cancel every active background tick loop,
ensuring clean process exit with no dangling asyncio tasks.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.simulation_manager import simulation_manager
from app.utils.config import get_settings
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager.

    Everything before ``yield`` runs at startup; everything after runs at
    shutdown.  Graceful shutdown cancels all active simulation background tasks
    so the process exits cleanly without asyncio warnings.
    """
    # ---- Startup ----
    logger.info("%s v%s starting up", settings.app_name, settings.app_version)
    yield
    # ---- Shutdown ----
    active = simulation_manager.active_simulations
    logger.info(
        "Shutting down — cancelling %d active simulation task(s): %s",
        len(active),
        active,
    )
    simulation_manager.stop_all()
    logger.info("All simulation tasks cancelled. Goodbye.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running", "docs": "/docs"}
