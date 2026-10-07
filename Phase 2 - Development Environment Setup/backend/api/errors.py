"""Consistent error responses (spec 14.11) and request-ID middleware."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or uuid.uuid4().hex


def _error(
    request: Request, status_code: int, code: str, message: str, field: str | None = None
) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=status_code,
        content={"error_code": code, "message": message, "field": field, "request_id": request_id},
        headers={REQUEST_ID_HEADER: request_id},
    )


def register_error_handling(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = uuid.uuid4().hex
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _error(request, exc.status_code, f"HTTP-{exc.status_code}", message)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = [str(part) for part in first.get("loc", ()) if part not in ("body", "query", "path")]
        return _error(
            request,
            422,
            "VAL-001",
            str(first.get("msg", "Invalid request")),
            field=".".join(loc) or None,
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id(request)
        logger.exception("Unhandled error", extra={"request_id": request_id})
        return _error(
            request,
            500,
            "SYS-999",
            f"Internal error. Quote request ID {request_id} when reporting this problem.",
        )
