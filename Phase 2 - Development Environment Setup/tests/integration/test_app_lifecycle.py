from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.core.config import Settings
from backend.core.database import build_sqlite_url
from backend.core.paths import PROJECT_ROOT
from backend.main import create_app


def test_startup_creates_directories_database_and_log(settings: Settings) -> None:
    with TestClient(create_app(settings)):
        assert settings.database_path.is_file()
        assert settings.logs_dir.is_dir() and settings.evidence_dir.is_dir()
    assert settings.log_file.is_file()  # written during startup/shutdown


def test_restart_keeps_database(settings: Settings) -> None:
    with TestClient(create_app(settings)):
        pass
    first = settings.database_path.stat().st_ino
    with TestClient(create_app(settings)):
        pass
    assert settings.database_path.stat().st_ino == first


def _alembic_config(settings: Settings) -> Config:
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.attributes["configure_logger"] = False
    cfg.attributes["sqlalchemy_url"] = build_sqlite_url(settings)
    return cfg


def test_alembic_is_configured_with_no_revisions_yet(settings: Settings) -> None:
    cfg = _alembic_config(settings)
    assert ScriptDirectory.from_config(cfg).get_heads() == []  # Phase 3 adds the first one
    command.upgrade(cfg, "head")  # must be a harmless no-op
    command.current(cfg)


def test_alembic_uses_spec_version_table_name(settings: Settings, tmp_path: Path) -> None:
    """A throwaway revision proves migrations apply and record in schema_migrations."""
    cfg = _alembic_config(settings)
    versions = tmp_path / "versions"
    versions.mkdir()
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    cfg.set_main_option("version_locations", str(versions))
    (versions / "0001_probe.py").write_text(
        "revision = '0001'\ndown_revision = None\nbranch_labels = None\ndepends_on = None\n"
        "from alembic import op\n"
        "def upgrade():\n    op.execute('CREATE TABLE probe (id INTEGER PRIMARY KEY)')\n"
        "def downgrade():\n    op.execute('DROP TABLE probe')\n",
        encoding="utf-8",
    )
    command.upgrade(cfg, "head")
    engine = create_engine(build_sqlite_url(settings))
    with engine.connect() as conn:
        assert (
            conn.execute(text("SELECT version_num FROM schema_migrations")).scalar_one() == "0001"
        )
    engine.dispose()
