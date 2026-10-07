# Development Guide

## Folder structure
| Folder | Purpose |
| --- | --- |
| `backend/api` | HTTP layer: routers (`v1/`), error handling, dependencies |
| `backend/core` | Configuration, paths, logging, SQLite engine/session |
| `backend/services` | Business logic (Phase 2: health checks only) |
| `backend/repositories` | All SQL/persistence access (Phase 2: diagnostics only) |
| `backend/models` | SQLAlchemy `Base` (tables arrive in Phase 3) |
| `backend/schemas` | Pydantic request/response models |
| `agent/*` | Automation runtime (empty until Phases 3-10) |
| `frontend` | Static HTML/CSS/JS served by the backend |
| `database` | SQLite file and `backups/` (git-ignored contents) |
| `migrations` | Alembic environment and `versions/` |
| `profiles`, `logs`, `evidence` | Runtime data (git-ignored; folders kept by `.gitkeep`) |
| `scripts` | Setup, start, diagnostics (scheduler/backup scripts arrive later) |
| `tests` | `unit/`, `api/`, `database/`, `integration/` |

Layering rule: API -> services -> repositories -> database. The API never talks SQL directly, and
GUI automation never runs inside a request handler (spec section 8.1).

## Dependencies
- `requirements.txt` - authoritative runtime pins. `requirements-dev.txt` - dev pins (includes the
  runtime file). `pyproject.toml` - Python constraint and tool settings; it reads runtime
  dependencies from `requirements.txt`.
- Update: change the pin in the requirements file, `python -m pip install -r requirements-dev.txt`,
  run `python -m pip check` and `pytest`, update `CHANGELOG.md`.
- Clean reproduction: new `.venv` -> `pip install -r requirements-dev.txt`.
- Transitive dependencies are resolved by pip. For an exact freeze of your machine:
  `python -m pip freeze > requirements.lock.txt` (not committed by default).

## Commands (venv active, from the project root)
```powershell
python -m backend                   # start API  (python -m backend --reload for development)
python -m pytest                    # all tests
python -m pytest tests\unit -q      # one folder
ruff check .                        # lint
black .                             # format
mypy backend scripts                # type check
python scripts\diagnostics\verify_environment.py
```

## Configuration
Settings load from defaults, then `.env`, then environment variables (`backend/core/config.py`).
Phase 2 keys: `APP_NAME, APP_ENV, APP_HOST, APP_PORT, DATABASE_PATH, LOG_LEVEL` plus optional path
and SQLite overrides listed in `.env.example`. Relative paths resolve against the project root.
A non-loopback `APP_HOST` is rejected unless `ALLOW_NON_LOCAL_BIND=true` (LAN access is out of scope).
Settings for browsers, profiles, file limits, scheduler, retry and power are reserved, not implemented.

## Database and migrations
- Engine setup: `backend/core/database.py` (foreign keys ON, WAL, busy timeout on every connection).
- Alembic reads the database URL from application settings (no URL in `alembic.ini`). The version
  table is named `schema_migrations`, matching spec section 13.1.
- Phase 3 workflow:
  ```powershell
  alembic revision --autogenerate -m "create core tables"
  alembic upgrade head
  alembic current
  ```
  Import every new model module in `backend/models/__init__.py` so autogenerate sees it. SQLite uses
  batch mode (`render_as_batch=True`). Take a backup before applying migrations to real data.

## Logging
JSON lines to the console and `logs/application.log` (daily rotation, 30 days). Values whose key or
`key=value` text looks like a password, token, cookie, secret, session or prompt are redacted.
Never log file contents or credentials.

## API conventions
All routes live under `/api/v1`. Errors use `{error_code, message, field, request_id}` and every
response carries `X-Request-ID`. `/api/v1/health/dependencies` is reserved for scheduler/target
checks (spec 14.1).

## What later phases add
Phase 3 models, queue and state machine; 4 targets/profiles; 5 browser adapters; 6 Claude Desktop;
7 files; 8 real UI; 9 scheduling; 10 sleep/wake; 11 retry/recovery; 12 monitoring; 13 packaging.
Phase 3 should also add same-origin protection for state-changing endpoints (spec NFR-022).
