"""Application configuration (spec section 23).

Priority (low -> high): built-in defaults, ``.env`` file, environment variables.
Phase 2 only implements the foundation settings. Settings for later phases
(browser executables, automation profiles, file limits, scheduler, retry, power)
are intentionally NOT defined yet; see ``.env.example`` for the reserved names.
"""

from __future__ import annotations

import ipaddress
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.paths import PROJECT_ROOT, resolve_project_path

LOOPBACK_NAMES = {"localhost"}


def is_loopback_host(host: str) -> bool:
    """True when ``host`` only accepts connections from this computer."""
    if host.lower() in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


class Settings(BaseSettings):
    """Validated runtime settings."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Required by the Phase 2 prompt ---
    app_name: str = "Local AI Task Automation System"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    database_path: Path = Path("database/automation.db")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- Foundation extras (spec section 23.2: paths, logging, SQLite) ---
    backup_dir: Path = Path("database/backups")
    logs_dir: Path = Path("logs")
    evidence_dir: Path = Path("evidence")
    profiles_dir: Path = Path("profiles")
    log_retention_days: int = Field(default=30, ge=1)
    sqlite_journal_mode: Literal["WAL", "DELETE"] = "WAL"
    sqlite_busy_timeout_ms: int = Field(default=5000, ge=0)

    # Safety switch: LAN exposure is out of scope (spec NFR-020, DEC-OPEN-006).
    allow_non_local_bind: bool = False

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("app_host")
    @classmethod
    def _strip_host(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("APP_HOST must not be empty")
        return value

    @model_validator(mode="after")
    def _normalise_and_check(self) -> Settings:
        # Higher-priority layers must not silently create unsafe settings (spec 23.1).
        if not self.allow_non_local_bind and not is_loopback_host(self.app_host):
            raise ValueError(
                f"APP_HOST={self.app_host!r} is not a loopback address. The API binds to "
                "localhost only by default; set ALLOW_NON_LOCAL_BIND=true to override "
                "deliberately (not supported in the initial release)."
            )
        self.database_path = resolve_project_path(self.database_path)
        self.backup_dir = resolve_project_path(self.backup_dir)
        self.logs_dir = resolve_project_path(self.logs_dir)
        self.evidence_dir = resolve_project_path(self.evidence_dir)
        self.profiles_dir = resolve_project_path(self.profiles_dir)
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def local_only(self) -> bool:
        return is_loopback_host(self.app_host)

    @property
    def log_file(self) -> Path:
        return self.logs_dir / "application.log"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings (cached). Tests should build ``Settings`` explicitly."""
    return Settings()
