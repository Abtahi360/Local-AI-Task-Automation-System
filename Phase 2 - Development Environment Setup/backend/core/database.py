"""SQLite connection foundation (spec sections 13.17 and NFR-027/NFR-030).

Every connection enforces foreign keys, uses a short busy timeout and (by
default) WAL journal mode. Business queries do NOT live here; they belong in
``backend/repositories``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import Settings

logger = logging.getLogger(__name__)


def build_sqlite_url(settings: Settings) -> URL:
    """Build a platform-safe SQLite URL (handles Windows drive letters)."""
    return URL.create("sqlite", database=str(settings.database_path))


def create_sqlite_engine(settings: Settings) -> Engine:
    """Create the engine and register per-connection PRAGMAs."""
    engine = create_engine(
        build_sqlite_url(settings),
        connect_args={
            "check_same_thread": False,  # FastAPI serves sync endpoints from a thread pool
            "timeout": settings.sqlite_busy_timeout_ms / 1000,
        },
    )
    journal_mode = settings.sqlite_journal_mode
    busy_timeout = settings.sqlite_busy_timeout_ms

    @event.listens_for(engine, "connect")
    def _configure_connection(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={int(busy_timeout)}")
            cursor.execute(f"PRAGMA journal_mode={journal_mode}")
            cursor.execute("PRAGMA synchronous=NORMAL")
        finally:
            cursor.close()

    return engine


class Database:
    """Owns the engine and session factory for one application instance."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine: Engine = create_sqlite_engine(settings)
        self.session_factory: sessionmaker[Session] = sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    def initialize(self) -> None:
        """Create the database file (and parent folder) if needed and verify connectivity."""
        self.settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.verify()
        logger.info(
            "SQLite database ready", extra={"database_file": self.settings.database_path.name}
        )

    def verify(self) -> None:
        """Open a connection and run ``SELECT 1``. Raises on failure."""
        from sqlalchemy import text

        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Transactional session scope: commit on success, rollback on error."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()
