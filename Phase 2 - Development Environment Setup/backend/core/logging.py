"""Structured (JSON-lines) logging foundation (spec section 21).

Each line contains timestamp, level, logger/component, message and, when present,
exception details. Known-sensitive values are redacted (spec NFR-019).
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Any

from backend.core.config import Settings

_HANDLER_TAG = "_lata_handler"
REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = (
    "password",
    "passwd",
    "secret",
    "token",
    "cookie",
    "authorization",
    "api_key",
    "apikey",
    "session",
    "prompt",
    "file_content",
)
_SENSITIVE_PATTERN = re.compile(
    r"(?i)\b(password|passwd|secret|token|cookie|authorization|api[_-]?key)\b(\s*[=:]\s*)"
    r"(\"[^\"]*\"|'[^']*'|\S+)"
)
_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


def redact(text: str) -> str:
    """Mask ``key=value`` / ``key: value`` pairs whose key looks sensitive."""
    return _SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", text)


def _redact_extra(key: str, value: Any) -> Any:
    if any(marker in key.lower() for marker in _SENSITIVE_KEYS):
        return REDACTED
    if isinstance(value, str):
        return redact(value)
    return value


class JsonFormatter(logging.Formatter):
    """Format records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": redact(record.getMessage()),
        }
        extras = {
            key: _redact_extra(key, value)
            for key, value in record.__dict__.items()
            if key not in _STANDARD_ATTRS
        }
        if extras:
            payload["context"] = extras
        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    """Install console + rotating-file handlers on the root logger (idempotent)."""
    shutdown_logging()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = JsonFormatter()
    console = logging.StreamHandler(sys.stderr)
    file_handler = TimedRotatingFileHandler(
        settings.log_file,
        when="midnight",
        backupCount=settings.log_retention_days,
        encoding="utf-8",
        delay=True,
    )
    root = logging.getLogger()
    root.setLevel(settings.log_level)
    # Keep third-party chatter out of the application log.
    for noisy in ("httpx", "httpx2", "httpcore", "alembic.runtime.plugins"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    for handler in (console, file_handler):
        handler.setFormatter(formatter)
        setattr(handler, _HANDLER_TAG, True)
        root.addHandler(handler)


def shutdown_logging() -> None:
    """Remove and close handlers installed by :func:`configure_logging`."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_TAG, False):
            root.removeHandler(handler)
            handler.close()
