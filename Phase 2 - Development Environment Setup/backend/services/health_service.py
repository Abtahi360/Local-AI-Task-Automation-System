"""Environment and dependency health checks (Phase 2 scope only).

No browser or desktop automation happens here. Playwright is only imported (and,
on request, its driver started) - no browser is launched and no site is visited.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import os
import platform
import sys
from pathlib import Path

from backend.schemas.health import (
    DesktopAutomationStatus,
    EnvironmentHealthResponse,
    PackageStatus,
    PlaywrightStatus,
    PythonStatus,
    Status,
)

MIN_PYTHON = (3, 12)
MAX_PYTHON_EXCLUSIVE = (3, 14)

# (distribution name, import name)
REQUIRED_PACKAGES: tuple[tuple[str, str], ...] = (
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("SQLAlchemy", "sqlalchemy"),
    ("alembic", "alembic"),
    ("pydantic", "pydantic"),
    ("pydantic-settings", "pydantic_settings"),
    ("playwright", "playwright"),
)


def _package_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _importable(module: str) -> bool:
    try:
        importlib.import_module(module)
    except Exception:
        return False
    return True


def check_python() -> PythonStatus:
    current = sys.version_info[:2]
    return PythonStatus(
        version=platform.python_version(),
        supported=MIN_PYTHON <= current < MAX_PYTHON_EXCLUSIVE,
        platform=sys.platform,
        in_virtualenv=sys.prefix != getattr(sys, "base_prefix", sys.prefix),
    )


def check_packages() -> list[PackageStatus]:
    results = []
    for distribution, module in REQUIRED_PACKAGES:
        version = _package_version(distribution)
        results.append(
            PackageStatus(
                name=distribution,
                required=True,
                installed=version is not None and _importable(module),
                version=version,
            )
        )
    return results


def playwright_browsers_path() -> Path:
    override = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if override and override != "0":
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "ms-playwright"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    return Path.home() / ".cache" / "ms-playwright"


def check_playwright(initialize_driver: bool = False) -> PlaywrightStatus:
    """Check Playwright import, optional driver start-up, and browser binaries.

    ``initialize_driver=True`` starts and stops the Playwright driver process
    (no browser is launched) and checks for the exact Chromium build this
    Playwright version expects. It is used by the verification script. Without it
    the check only looks for a ``chromium-*`` folder, which is approximate (a
    folder from another Playwright version also matches).
    """
    version = _package_version("playwright")
    if version is None or not _importable("playwright.sync_api"):
        return PlaywrightStatus(
            importable=False, version=version, error="playwright not importable"
        )

    browsers_path = playwright_browsers_path()
    chromium_installed = browsers_path.is_dir() and any(browsers_path.glob("chromium-*"))
    status = PlaywrightStatus(
        importable=True,
        version=version,
        browsers_path=str(browsers_path),
        chromium_installed=chromium_installed,
    )
    if initialize_driver:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                # Exact binary this Playwright version expects (not just any chromium-* folder).
                expected = Path(playwright.chromium.executable_path)
            status.driver_initialized = True
            status.chromium_installed = expected.exists()
        except Exception as exc:  # pragma: no cover - environment dependent
            status.driver_initialized = False
            status.error = f"{type(exc).__name__}: {exc}"
    return status


def check_desktop_automation() -> DesktopAutomationStatus:
    required = sys.platform == "win32"
    version = _package_version("pywinauto")
    return DesktopAutomationStatus(
        required_on_this_platform=required,
        installed=version is not None,
        version=version,
    )


def check_environment(initialize_playwright_driver: bool = False) -> EnvironmentHealthResponse:
    python_status = check_python()
    packages = check_packages()
    playwright_status = check_playwright(initialize_playwright_driver)
    desktop = check_desktop_automation()

    notes: list[str] = []
    errors = 0
    degraded = 0

    if not python_status.supported:
        errors += 1
        notes.append("Python version is outside the supported range (>=3.12,<3.14).")
    if not python_status.in_virtualenv:
        degraded += 1
        notes.append("Not running inside a virtual environment (.venv is recommended).")
    if any(not p.installed for p in packages):
        errors += 1
        notes.append("One or more required packages are missing; run the setup script.")
    if playwright_status.driver_initialized is False:
        errors += 1
        notes.append("Playwright driver failed to initialize.")
    if playwright_status.importable and not playwright_status.chromium_installed:
        degraded += 1
        notes.append(
            "Playwright Chromium binary not found (optional in Phase 2): "
            "run 'python -m playwright install chromium'."
        )
    if desktop.required_on_this_platform and not desktop.installed:
        errors += 1
        notes.append("pywinauto is required on Windows but is not installed.")
    if not desktop.required_on_this_platform:
        notes.append("pywinauto is Windows-only and is not required on this platform.")

    status: Status = "error" if errors else "degraded" if degraded else "ok"
    return EnvironmentHealthResponse(
        status=status,
        configuration_loaded=True,
        python=python_status,
        packages=packages,
        playwright=playwright_status,
        desktop_automation=desktop,
        notes=notes,
    )
