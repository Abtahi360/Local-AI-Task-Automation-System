"""Project path helpers and runtime-directory initialisation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from backend.core.config import Settings

# backend/core/paths.py -> project root is two levels above the package folder.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"
MIGRATIONS_DIR: Path = PROJECT_ROOT / "migrations"


def resolve_project_path(value: str | Path, root: Path = PROJECT_ROOT) -> Path:
    """Return an absolute, normalised path; relative values are anchored at ``root``."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return Path(path.resolve())


def ensure_runtime_directories(settings: Settings) -> list[Path]:
    """Create every runtime directory the application needs. Safe to call repeatedly.

    Never deletes or modifies existing content.
    """
    directories = [
        settings.database_path.parent,
        settings.backup_dir,
        settings.logs_dir,
        settings.evidence_dir,
        settings.profiles_dir,
    ]
    created: list[Path] = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created
