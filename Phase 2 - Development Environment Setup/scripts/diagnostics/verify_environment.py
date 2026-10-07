"""Verify the Phase 2 development environment and print a PASS/FAIL summary.

Usage (from the project root, with the venv active):
    python scripts/diagnostics/verify_environment.py
Exit code 0 = environment usable; 1 = something required is missing.
Optional items (for example the Playwright Chromium binary) only produce warnings.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.core.config import Settings  # noqa: E402
from backend.core.database import Database  # noqa: E402
from backend.services import database_health_service, health_service  # noqa: E402


def line(level: str, text: str) -> None:
    print(f"[{level:^4}] {text}")


def main() -> int:
    failures = 0

    try:
        settings = Settings()
        line("OK", f"Configuration loaded (host {settings.app_host}, port {settings.app_port})")
        if settings.local_only:
            line("OK", "API is configured for localhost only")
        else:
            line("WARN", "API host is not loopback (ALLOW_NON_LOCAL_BIND is set)")
    except Exception as exc:
        line("FAIL", f"Configuration could not be loaded: {exc}")
        return 1

    env = health_service.check_environment(initialize_playwright_driver=True)
    py = env.python
    if py.supported:
        line("OK", f"Python {py.version} ({py.platform})")
    else:
        failures += 1
        line("FAIL", f"Python {py.version} is outside the supported range >=3.12,<3.14")
    line("OK" if py.in_virtualenv else "WARN", "Running inside a virtual environment")

    for package in env.packages:
        if package.installed:
            line("OK", f"{package.name} {package.version}")
        else:
            failures += 1
            line("FAIL", f"{package.name} is not installed")

    pw = env.playwright
    if pw.driver_initialized:
        line("OK", f"Playwright {pw.version} driver initialises")
    else:
        failures += 1
        line("FAIL", f"Playwright driver did not initialise: {pw.error}")
    line(
        "OK" if pw.chromium_installed else "WARN",
        (
            "Playwright Chromium binary installed"
            if pw.chromium_installed
            else "Playwright Chromium binary not installed "
            "(run: python -m playwright install chromium)"
        ),
    )

    desktop = env.desktop_automation
    if desktop.required_on_this_platform:
        if desktop.installed:
            line("OK", f"pywinauto {desktop.version}")
        else:
            failures += 1
            line("FAIL", "pywinauto is not installed (required on Windows)")
    else:
        line("INFO", "pywinauto is Windows-only; skipped on this platform")

    database = Database(settings)
    try:
        database.initialize()
        result = database_health_service.check_database(database)
    finally:
        database.dispose()
    if result.status == "ok":
        line(
            "OK",
            f"SQLite {result.sqlite_version}, journal={result.journal_mode}, "
            f"foreign_keys={'ON' if result.foreign_keys_enabled else 'OFF'}",
        )
    else:
        failures += 1
        line("FAIL", f"SQLite check failed: {result.error}")

    print()
    if failures:
        print(f"RESULT: FAIL ({failures} required check(s) failed)")
        return 1
    print("RESULT: PASS - Phase 2 development environment is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
