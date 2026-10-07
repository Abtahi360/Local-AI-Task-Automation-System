"""Health-check response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Status = Literal["ok", "degraded", "error"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app_name: str
    version: str
    environment: str
    timestamp: datetime


class DatabaseHealthResponse(BaseModel):
    status: Literal["ok", "error"]
    connected: bool
    engine: str = "sqlite"
    database_file: str
    database_file_exists: bool
    sqlite_version: str | None = None
    journal_mode: str | None = None
    foreign_keys_enabled: bool | None = None
    busy_timeout_ms: int | None = None
    error: str | None = None


class PackageStatus(BaseModel):
    name: str
    required: bool
    installed: bool
    version: str | None = None


class PythonStatus(BaseModel):
    version: str
    supported: bool
    platform: str
    in_virtualenv: bool


class PlaywrightStatus(BaseModel):
    importable: bool
    version: str | None = None
    driver_initialized: bool | None = None
    browsers_path: str | None = None
    chromium_installed: bool = False
    error: str | None = None


class DesktopAutomationStatus(BaseModel):
    package: str = "pywinauto"
    required_on_this_platform: bool
    installed: bool
    version: str | None = None


class EnvironmentHealthResponse(BaseModel):
    status: Status
    configuration_loaded: bool
    python: PythonStatus
    packages: list[PackageStatus]
    playwright: PlaywrightStatus
    desktop_automation: DesktopAutomationStatus
    notes: list[str]
