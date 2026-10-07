"""Database health check built on the repository layer."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from backend.core.database import Database
from backend.repositories.database_repository import DatabaseDiagnosticsRepository
from backend.schemas.health import DatabaseHealthResponse

logger = logging.getLogger(__name__)


def _first_line(exc: Exception) -> str:
    lines = str(exc).splitlines()
    return f"{type(exc).__name__}: {lines[0] if lines else 'error'}"


def check_database(database: Database) -> DatabaseHealthResponse:
    path = database.settings.database_path
    try:
        with database.session() as session:
            diagnostics = DatabaseDiagnosticsRepository(session).read()
    except SQLAlchemyError as exc:
        logger.exception("Database health check failed")
        return DatabaseHealthResponse(
            status="error",
            connected=False,
            database_file=path.name,
            database_file_exists=path.exists(),
            error=_first_line(exc),
        )
    healthy = diagnostics.foreign_keys_enabled
    return DatabaseHealthResponse(
        status="ok" if healthy else "error",
        connected=True,
        database_file=path.name,
        database_file_exists=path.exists(),
        sqlite_version=diagnostics.sqlite_version,
        journal_mode=diagnostics.journal_mode,
        foreign_keys_enabled=diagnostics.foreign_keys_enabled,
        busy_timeout_ms=diagnostics.busy_timeout_ms,
        error=None if healthy else "Foreign-key enforcement is not enabled",
    )
