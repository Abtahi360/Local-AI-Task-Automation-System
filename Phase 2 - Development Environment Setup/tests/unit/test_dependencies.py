import importlib
import sys

import pytest

from backend.services import health_service


@pytest.mark.parametrize(
    "module",
    ["fastapi", "uvicorn", "sqlalchemy", "alembic", "pydantic", "pydantic_settings", "playwright"],
)
def test_required_modules_import(module: str) -> None:
    importlib.import_module(module)


def test_playwright_sync_api_imports() -> None:
    importlib.import_module("playwright.sync_api")


def test_playwright_driver_initializes_without_launching_a_browser() -> None:
    status = health_service.check_playwright(initialize_driver=True)
    assert status.importable is True
    assert status.driver_initialized is True, status.error


@pytest.mark.skipif(sys.platform != "win32", reason="pywinauto is Windows-only")
def test_pywinauto_installed_on_windows() -> None:
    importlib.import_module("pywinauto")


def test_python_version_is_supported() -> None:
    assert health_service.check_python().supported


def test_all_required_packages_report_installed() -> None:
    missing = [p.name for p in health_service.check_packages() if not p.installed]
    assert missing == []


def test_environment_check_has_no_error_status() -> None:
    assert health_service.check_environment().status in {"ok", "degraded"}
