import json
import logging

from backend.core.config import Settings
from backend.core.logging import REDACTED, configure_logging, redact, shutdown_logging


def test_redact_masks_sensitive_pairs() -> None:
    text = "login password=hunter2 token: abc123 cookie='a b' ok=1"
    cleaned = redact(text)
    assert "hunter2" not in cleaned and "abc123" not in cleaned and "a b" not in cleaned
    assert "ok=1" in cleaned
    assert REDACTED in cleaned


def test_log_file_is_json_with_required_fields(settings: Settings) -> None:
    configure_logging(settings)
    try:
        logging.getLogger("tests.component").info(
            "hello password=secret1", extra={"session_cookie": "zzz", "task_id": "t1"}
        )
        try:
            raise ValueError("boom")
        except ValueError:
            logging.getLogger("tests.component").exception("failed")
    finally:
        shutdown_logging()

    lines = settings.log_file.read_text(encoding="utf-8").splitlines()
    first, second = (json.loads(line) for line in lines[:2])
    assert {"timestamp", "level", "component", "message"} <= first.keys()
    assert first["component"] == "tests.component"
    assert "secret1" not in first["message"]
    assert first["context"]["session_cookie"] == REDACTED
    assert first["context"]["task_id"] == "t1"
    assert "ValueError: boom" in second["exception"]


def test_configure_logging_is_idempotent(settings: Settings) -> None:
    root = logging.getLogger()
    before = len(root.handlers)
    configure_logging(settings)
    configure_logging(settings)
    try:
        assert len(root.handlers) == before + 2  # console + file, not duplicated
    finally:
        shutdown_logging()
    assert len(root.handlers) == before
