"""System-information schema."""

from __future__ import annotations

from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    phase: str
    environment: str
    python_version: str
    platform: str
    host: str
    port: int
    local_only: bool
    api_prefix: str
