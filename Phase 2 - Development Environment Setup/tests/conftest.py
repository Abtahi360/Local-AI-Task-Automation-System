"""Shared fixtures. Tests never touch the real .env, database, or logs."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings that point entirely inside a temporary directory."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_env="test",
        database_path=tmp_path / "database" / "test.db",
        backup_dir=tmp_path / "database" / "backups",
        logs_dir=tmp_path / "logs",
        evidence_dir=tmp_path / "evidence",
        profiles_dir=tmp_path / "profiles",
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """A TestClient with the app lifespan running (database initialised)."""
    with TestClient(create_app(settings)) as test_client:
        yield test_client
