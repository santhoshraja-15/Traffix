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

import sys
sys.stdout.reconfigure(encoding='utf-8')

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ml.model_registry import model_registry
from app.ml.ml_adapter import TrafficModelAdapter
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

    # 🚨 LOCKING V15 XGBOOST INTO RAM 🚨
    print("🚨 LOCKING V15 XGBOOST INTO RAM 🚨")
    app.state.ml_engine = TrafficModelAdapter()
    if not app.state.ml_engine.is_ready:
        raise RuntimeError(
            "V15 XGBoost model failed to load. Place "
            "trafficx_xgboost_v15_risk_escalation.json under app/ml/weights/."
        )
    print("🟢 V15 BRAIN ONLINE 🟢")
    logger.info("TrafficModelAdapter status: %s", repr(app.state.ml_engine))

    # Inject the V15 engine into the simulation manager so the tick loop can
    # call predict_batch() without going through app.state.
    simulation_manager.set_ml_engine(app.state.ml_engine)

    # Attempt SUMO bridge connection.
    # If SUMO is not running / traci not installed, the bridge gracefully
    # falls back to mock mode — the server always starts regardless.
    try:
        from app.integrations.sumo_bridge import SumoBridge, SUMO_AVAILABLE
        if SUMO_AVAILABLE:
            _bridge = SumoBridge()
            connected = _bridge.connect()
            if connected:
                simulation_manager.set_sumo_bridge(_bridge)
                app.state.sumo_bridge = _bridge
                print("🔌 SUMO BRIDGE ONLINE — TraCI executor pinned to 1 thread 🔌")
            else:
                app.state.sumo_bridge = None
                print("⚠️  SUMO bridge: connect() failed — mock mode active.")
        else:
            app.state.sumo_bridge = None
            print("⚠️  SUMO bridge: traci not installed — mock mode active.")
    except Exception as _bridge_exc:
        logger.warning("SUMO bridge startup failed (non-fatal): %s", _bridge_exc)
        app.state.sumo_bridge = None

    if model_registry.is_available("v16_risk"):
        model_registry.load("v16_risk")

    yield

    # ---- Shutdown ----
    print("🛑 Unloading V15 Brain")
    simulation_manager.stop_all()

    # Cleanly drain the dedicated SUMO executor thread.
    _bridge = getattr(app.state, "sumo_bridge", None)
    if _bridge is not None:
        _bridge.shutdown()

    app.state.ml_engine = None
    app.state.sumo_bridge = None
    logger.info("All simulation tasks cancelled. AI unloaded. Goodbye.")




app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

_cors_origins = [origin for origin in settings.cors_allow_origins if origin != "*"]
if not _cors_origins:
    _cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running", "docs": "/docs"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Root health probe used by the React dashboard connectivity check."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }
