from pathlib import Path

from backend.core.config import Settings
from backend.core.paths import ensure_runtime_directories


def test_ensure_runtime_directories_creates_all(settings: Settings) -> None:
    created = ensure_runtime_directories(settings)
    assert {p.name for p in created} >= {"database", "backups", "logs", "evidence", "profiles"}
    assert all(p.is_dir() for p in created)


def test_ensure_runtime_directories_is_idempotent_and_keeps_files(settings: Settings) -> None:
    ensure_runtime_directories(settings)
    marker: Path = settings.logs_dir / "keep.txt"
    marker.write_text("do not delete", encoding="utf-8")
    ensure_runtime_directories(settings)
    assert marker.read_text(encoding="utf-8") == "do not delete"
