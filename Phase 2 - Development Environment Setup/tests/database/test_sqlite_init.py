import sqlite3

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.core.config import Settings
from backend.core.database import Database, build_sqlite_url
from backend.models import Base
from backend.repositories.database_repository import DatabaseDiagnosticsRepository


@pytest.fixture
def database(settings: Settings):
    db = Database(settings)
    yield db
    db.dispose()


def test_initialize_creates_file_and_parent_directory(
    settings: Settings, database: Database
) -> None:
    assert not settings.database_path.exists()
    database.initialize()
    assert settings.database_path.is_file()


def test_initialize_is_idempotent_and_keeps_data(settings: Settings, database: Database) -> None:
    database.initialize()
    with database.session() as s:
        s.execute(text("CREATE TABLE keepme (id INTEGER PRIMARY KEY)"))
        s.execute(text("INSERT INTO keepme VALUES (42)"))
    database.initialize()
    with database.session() as s:
        assert s.execute(text("SELECT id FROM keepme")).scalar_one() == 42


def test_pragmas_foreign_keys_wal_busy_timeout(settings: Settings, database: Database) -> None:
    database.initialize()
    with database.session() as session:
        diagnostics = DatabaseDiagnosticsRepository(session).read()
    assert diagnostics.foreign_keys_enabled is True  # NFR-027
    assert diagnostics.journal_mode == "WAL"  # NFR-030
    assert diagnostics.busy_timeout_ms == settings.sqlite_busy_timeout_ms


def test_foreign_key_violation_is_rejected(database: Database) -> None:
    database.initialize()
    with database.session() as s:
        s.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY)"))
        s.execute(
            text(
                "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER "
                "REFERENCES parent(id))"
            )
        )
    with pytest.raises(IntegrityError), database.session() as s:
        s.execute(text("INSERT INTO child (id, parent_id) VALUES (1, 999)"))  # AC-022


def test_session_rolls_back_on_error(database: Database) -> None:
    database.initialize()
    with database.session() as s:
        s.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY)"))
    with pytest.raises(RuntimeError), database.session() as s:
        s.execute(text("INSERT INTO t VALUES (1)"))
        raise RuntimeError("fail")
    with database.session() as s:
        assert s.execute(text("SELECT COUNT(*) FROM t")).scalar_one() == 0


def test_url_uses_configured_path(settings: Settings) -> None:
    url = build_sqlite_url(settings)
    assert url.drivername == "sqlite"
    assert url.database == str(settings.database_path)


def test_no_tables_are_created_in_phase_2(settings: Settings, database: Database) -> None:
    """Phase 2 provides the foundation only; the real schema arrives in Phase 3."""
    assert Base.metadata.tables == {}
    database.initialize()
    conn = sqlite3.connect(settings.database_path)
    try:
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
    finally:
        conn.close()


def test_verify_fails_when_path_is_a_directory(settings: Settings, tmp_path) -> None:
    broken = settings.model_copy(update={"database_path": tmp_path})
    db = Database(broken)
    try:
        with pytest.raises(SQLAlchemyError):
            db.verify()
    finally:
        db.dispose()
