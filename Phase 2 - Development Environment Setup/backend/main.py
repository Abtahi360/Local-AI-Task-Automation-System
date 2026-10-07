"""FastAPI application factory and ASGI entry point.

Run locally with:  python -m backend          (or: python -m uvicorn backend.main:app)
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from backend import __version__
from backend.api.errors import register_error_handling
from backend.api.router import api_router
from backend.core.config import Settings, get_settings
from backend.core.database import Database
from backend.core.logging import configure_logging, shutdown_logging
from backend.core.paths import FRONTEND_DIR, ensure_runtime_directories

logger = logging.getLogger("backend.lifecycle")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application. Tests pass explicit ``Settings``; production uses ``.env``."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        ensure_runtime_directories(settings)
        configure_logging(settings)
        database = Database(settings)
        app.state.database = database
        app.state.database_startup_error = None
        try:
            database.initialize()
        except (SQLAlchemyError, OSError) as exc:
            # Stay up so /api/v1/health/database can report the problem clearly.
            app.state.database_startup_error = f"{type(exc).__name__}: {exc}"
            logger.exception("Database initialization failed")
        logger.info(
            "Application started",
            extra={"environment": settings.app_env, "host": settings.app_host},
        )
        try:
            yield
        finally:
            database.dispose()
            logger.info("Application stopped")
            shutdown_logging()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.state.settings = settings

    register_error_handling(app)
    app.include_router(api_router)

    if FRONTEND_DIR.is_dir():
        app.mount("/styles", StaticFiles(directory=FRONTEND_DIR / "styles"), name="styles")
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
