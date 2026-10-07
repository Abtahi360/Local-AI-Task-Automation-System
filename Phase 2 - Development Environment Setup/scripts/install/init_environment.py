"""Initialise runtime directories and the SQLite database. Safe to run repeatedly.

Usage (from the project root, with the venv active):
    python scripts/install/init_environment.py
Never deletes or overwrites existing data.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from backend.core.config import Settings  # noqa: E402
from backend.core.database import Database  # noqa: E402
from backend.core.paths import ensure_runtime_directories  # noqa: E402


def main() -> int:
    try:
        settings = Settings()
    except Exception as exc:
        print(f"[FAIL] Configuration could not be loaded: {exc}")
        return 1
    print("[ OK ] Configuration loaded")

    for directory in ensure_runtime_directories(settings):
        print(f"[ OK ] Directory ready: {directory}")

    database = Database(settings)
    try:
        database.initialize()
    except (SQLAlchemyError, OSError) as exc:
        print(f"[FAIL] SQLite initialisation failed: {exc}")
        return 1
    finally:
        database.dispose()
    print(f"[ OK ] SQLite database ready: {settings.database_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
