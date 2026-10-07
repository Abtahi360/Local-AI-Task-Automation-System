"""Shared API schemas, including the consistent error shape (spec 14.11)."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    field: str | None = None
    request_id: str
