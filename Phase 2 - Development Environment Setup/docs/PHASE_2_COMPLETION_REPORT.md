# Phase 2 Completion Report - Development Environment Setup

| Field | Value |
| --- | --- |
| Project | Local AI Task Automation System |
| Phase | 2 - Development Environment Setup |
| Source of truth | `SYSTEM_SPECIFICATION.pdf` v1.0 |
| Version | 0.2.0 |
| **Conclusion** | **PASS on the build/verification environment (Linux). Windows-side confirmation by the user is still required** (see section 9). |

## 1. Scope
Foundation only: skeleton, Python environment, dependency management, FastAPI foundation, SQLite
connection foundation, SQLAlchemy and Alembic foundations, configuration, logging, health checks,
setup/start scripts, test framework, documentation. Nothing from Phase 3+ is implemented.

## 2. Implemented deliverables
1. Project skeleton matching the approved layout (including empty `agent/*` packages).
2. Pinned dependencies: `requirements.txt`, `requirements-dev.txt`; `pyproject.toml` holds the Python
   constraint and tool settings and reads runtime dependencies from `requirements.txt`.
3. FastAPI app factory with lifespan startup/shutdown, request IDs and a consistent error shape.
4. Endpoints: `GET /api/v1/health`, `/api/v1/health/database`, `/api/v1/health/environment`,
   `/api/v1/system/info`, and `/` (status page).
5. SQLite engine: foreign keys ON, WAL, busy timeout, per-connection PRAGMAs; session scope.
6. SQLAlchemy `Base` (no tables); Alembic configured (no revisions; version table `schema_migrations`).
7. Settings (`.env` + environment variables); loopback-only host enforced.
8. JSON logging with redaction, daily rotation, 30-day retention.
9. `setup.ps1`, `setup.bat`, `start.ps1`, `start.bat`, `init_environment.py`, `verify_environment.py`.
10. Minimal HTML/CSS/JS status page. 11. pytest suite. 12. README, SETUP, DEVELOPMENT, TROUBLESHOOTING, CHANGELOG.

## 3. Versions
| Item | Version |
| --- | --- |
| Python (verified) | 3.12.3 (allowed range `>=3.12,<3.14`; 3.13 not verified) |
| FastAPI / Starlette (transitive) | 0.142.2 / 1.7.0 |
| Uvicorn | 0.54.0 |
| Pydantic / pydantic-settings | 2.13.5 / 2.15.0 |
| SQLAlchemy | 2.1.3 |
| Alembic | 1.20.0 |
| Playwright | 1.63.0 |
| pywinauto (Windows only) | 0.6.9 (wheel confirmed available; not installed/imported on Linux) |
| pytest / pytest-asyncio | 9.1.1 / 1.4.0 |
| httpx / httpx2 | 0.28.1 / 2.13.1 |
| ruff / black / mypy | 0.16.10 / 26.10.0 / 2.4.0 |

Selection: the latest releases available on PyPI on 2026-10-06 were installed together, then pinned
only after `pip check`, the full test suite, a real migration probe, and a live server run all passed.
`httpx2` was added because Starlette 1.7's `TestClient` deprecates plain `httpx`.

## 4. Verification performed (Linux container, Ubuntu 24, Python 3.12.3)
| Check | Result |
| --- | --- |
| Clean copy, new venv, `pip install -r requirements-dev.txt` | Succeeded (~10 s); `pip check`: no broken requirements |
| `scripts/install/init_environment.py` | Directories and `automation.db` created |
| `scripts/diagnostics/verify_environment.py` | `RESULT: PASS` (Chromium line WARN, see below) |
| `pytest` | **106 passed, 1 skipped** (Windows-only pywinauto test) |
| `ruff check`, `black --check`, `mypy backend scripts` | All clean |
| Real server `python -m backend`; curl of health, database, system/info, `/`, 404 | All correct; 404 uses the standard error JSON |
| Socket check | Listening on 127.0.0.1:8000 only |
| Alembic `current`/`upgrade head` with no revisions; throwaway revision | No-op OK; revision applied and recorded in `schema_migrations` |
| Git: `.gitignore` check | `.env`, DB/WAL, logs, profiles, evidence, `.venv`, caches ignored; `.gitkeep` files tracked |
| PowerShell `setup.ps1` and `start.ps1` | Syntax parsed OK with the PowerShell 7.4.6 parser |
| Requirements | No cloud SDK, Redis, Docker or database-server package |

## 5. Files created
Listed in the delivered archive; see the project tree in the hand-off message. Additions beyond the
requested tree: `alembic.ini`, `.gitattributes`, `scripts/start.bat`, `scripts/install/init_environment.py`,
`scripts/diagnostics/verify_environment.py`, `backend/api/{deps,errors,prefix,router}.py`,
`backend/api/v1/`, `backend/__main__.py`, `database/backups/.gitkeep`.

## 6. Deviations and decisions to confirm
- `/api/v1/health/environment` was added; `/api/v1/health/dependencies` stays reserved for scheduler/target checks (spec 14.1).
- Alembic version table is named `schema_migrations` (spec 13.1).
- `httpx2` added alongside `httpx` (see section 3).
- Non-loopback `APP_HOST` is rejected unless `ALLOW_NON_LOCAL_BIND=true` (spec NFR-020 / DEC-OPEN-006).
- Only Playwright Chromium is downloaded (test browser). Real targets use installed Chrome/Brave/Edge later.
- Scripts call `.venv\Scripts\python.exe` directly instead of `Activate.ps1`; isolation is identical.

## 7. Known limitations
- **Not executed on Windows**: `setup.ps1`, `setup.bat`, `start.ps1`, `start.bat` (only syntax-parsed), Windows paths, `pywinauto` install/import, the Windows-only test.
- **Playwright Chromium binary download was not performed** here (network allow-list). The driver starts correctly; the exact Chromium build is reported as not installed, which is a WARN, not a failure.
- Python 3.13 not exercised. No browser-based test of the status page was run (the page's files are served and the JSON APIs it calls were verified).
- State-changing request protection (NFR-022) is deferred to Phase 3 because no state-changing endpoints exist.

## 8. Not implemented (intentionally)
Tasks/CRUD, state machine, queue, scheduler, browser/desktop adapters, Claude automation, file
attachment, retries, sleep/wake, full schema, dashboard, packaging.

## 9. Remaining user-side checks
Run `scripts\install\setup.ps1` on the Windows computer and expect `SETUP COMPLETE.`; run
`scripts\start.ps1` and open <http://127.0.0.1:8000>; confirm **ONLINE / CONNECTED / READY**; run
`pytest` (expect all tests passed; on Windows the pywinauto test runs instead of being skipped). Report any error text back.

## 10. Phase 3 readiness
Ready once section 9 is confirmed: the persistence layer, migration tooling, test fixtures and
layering exist; Phase 3 adds models, the first migration, repositories, queue and state machine.
