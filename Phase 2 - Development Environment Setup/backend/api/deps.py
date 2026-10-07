"""FastAPI dependencies: application-scoped settings and database."""

from __future__ import annotations

from fastapi import Request

from backend.core.config import Settings
from backend.core.database import Database


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database
