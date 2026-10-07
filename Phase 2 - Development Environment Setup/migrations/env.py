"""Alembic environment (SQLite, batch mode, URL from application settings)."""

from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine

from backend.core.config import Settings
from backend.core.database import build_sqlite_url
from backend.models import Base

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# Spec section 13.1/13.13 names the Alembic version table "schema_migrations".
VERSION_TABLE = "schema_migrations"


def _database_url():
    # An explicit URL (used by tests via config.attributes) wins over the settings.
    explicit = config.attributes.get("sqlalchemy_url")
    return explicit if explicit is not None else build_sqlite_url(Settings())


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url().render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _database_url()
    if url.database:  # a fresh checkout may not have the database folder yet
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite cannot ALTER most things in place
            compare_type=True,
            version_table=VERSION_TABLE,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
