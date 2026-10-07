"""The Phase 2 skeleton must match the approved layout."""

import tomllib
from pathlib import Path

import pytest

from backend import __version__
from backend.core.paths import PROJECT_ROOT

REQUIRED_DIRS = [
    "backend/api",
    "backend/core",
    "backend/services",
    "backend/repositories",
    "backend/models",
    "backend/schemas",
    "agent/executors",
    "agent/browser",
    "agent/desktop",
    "agent/adapters",
    "agent/queue",
    "agent/power",
    "agent/recovery",
    "frontend/styles",
    "frontend/assets",
    "database/backups",
    "migrations/versions",
    "config",
    "profiles",
    "logs",
    "evidence",
    "scripts/install",
    "scripts/scheduler",
    "scripts/backup",
    "scripts/diagnostics",
    "tests/unit",
    "tests/api",
    "tests/database",
    "tests/integration",
    "docs",
    "packaging",
]
REQUIRED_FILES = [
    "backend/main.py",
    "frontend/index.html",
    ".gitignore",
    ".env.example",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "alembic.ini",
    "migrations/env.py",
    "scripts/install/setup.ps1",
    "scripts/install/setup.bat",
    "scripts/start.ps1",
    "docs/SETUP.md",
    "docs/DEVELOPMENT.md",
    "docs/TROUBLESHOOTING.md",
    "docs/PHASE_2_COMPLETION_REPORT.md",
]


@pytest.mark.parametrize("relative", REQUIRED_DIRS)
def test_required_directory_exists(relative: str) -> None:
    assert (PROJECT_ROOT / relative).is_dir()


@pytest.mark.parametrize("relative", REQUIRED_FILES)
def test_required_file_exists(relative: str) -> None:
    assert (PROJECT_ROOT / relative).is_file()


def test_pyproject_constraints_and_version() -> None:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["requires-python"] == ">=3.12,<3.14"
    assert data["project"]["version"] == __version__


def test_requirements_are_pinned_and_cloud_free() -> None:
    forbidden = ("redis", "psycopg", "postgres", "mysql", "pymysql", "docker", "boto3", "azure")
    for name in ("requirements.txt", "requirements-dev.txt"):
        lines = (PROJECT_ROOT / name).read_text(encoding="utf-8").splitlines()
        specs = [ln for ln in lines if ln.strip() and not ln.startswith(("#", "-r"))]
        assert all("==" in ln for ln in specs), name
        assert not [ln for ln in specs if any(f in ln.lower() for f in forbidden)]


def test_env_example_has_no_secrets() -> None:
    text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8").lower()
    for word in ("password=", "token=", "secret=", "cookie="):
        assert word not in text
    assert "app_host=127.0.0.1" in text


def test_gitignore_excludes_runtime_data() -> None:
    text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (
        ".venv/",
        "__pycache__/",
        "*.pyc",
        ".env",
        "database/*.db",
        "/logs/*",
        "/evidence/*",
        "/profiles/*",
        ".idea/",
        ".vscode/",
    ):
        assert entry in text


def test_gitkeep_files_present() -> None:
    for relative in (
        "database",
        "database/backups",
        "config",
        "profiles",
        "logs",
        "evidence",
        "packaging",
        "migrations/versions",
    ):
        assert Path(PROJECT_ROOT / relative / ".gitkeep").is_file()
