"""Health endpoints: GET /api/v1/health, /health/database, /health/environment.

``/health/dependencies`` (scheduler, targets) is reserved by the specification
(section 14.1) for later phases and is intentionally not implemented here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend import __version__
from backend.api.deps import get_app_settings, get_database
from backend.core.config import Settings
from backend.core.database import Database
from backend.schemas.health import (
    DatabaseHealthResponse,
    EnvironmentHealthResponse,
    HealthResponse,
)
from backend.services import database_health_service, health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_app_settings)]) -> HealthResponse:
    """Liveness: the API process is up and configuration loaded."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=__version__,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    responses={503: {"model": DatabaseHealthResponse}},
)
def health_database(database: Annotated[Database, Depends(get_database)]) -> JSONResponse:
    """Readiness of the SQLite database (503 when it cannot be used)."""
    result = database_health_service.check_database(database)
    return JSONResponse(
        status_code=200 if result.status == "ok" else 503,
        content=result.model_dump(mode="json"),
    )


@router.get("/environment", response_model=EnvironmentHealthResponse)
def health_environment() -> EnvironmentHealthResponse:
    """Python, required packages, Playwright and desktop-automation dependency status."""
    return health_service.check_environment()
