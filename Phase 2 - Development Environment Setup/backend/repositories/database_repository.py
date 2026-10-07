"""Read-only database diagnostics repository.

Keeps raw SQL/PRAGMA details out of the API and service layers. Phase 3 adds the
task/queue repositories next to this file.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DatabaseDiagnostics:
    sqlite_version: str
    journal_mode: str
    foreign_keys_enabled: bool
    busy_timeout_ms: int


class DatabaseDiagnosticsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def read(self) -> DatabaseDiagnostics:
        version = self._session.execute(text("SELECT sqlite_version()")).scalar_one()
        journal_mode = self._session.execute(text("PRAGMA journal_mode")).scalar_one()
        foreign_keys = self._session.execute(text("PRAGMA foreign_keys")).scalar_one()
        busy_timeout = self._session.execute(text("PRAGMA busy_timeout")).scalar_one()
        return DatabaseDiagnostics(
            sqlite_version=str(version),
            journal_mode=str(journal_mode).upper(),
            foreign_keys_enabled=bool(foreign_keys),
            busy_timeout_ms=int(busy_timeout),
        )
