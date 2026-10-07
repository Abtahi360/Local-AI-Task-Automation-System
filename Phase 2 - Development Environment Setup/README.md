# Local AI Task Automation System

A **local-first Windows application** that lets one user create, schedule, execute, monitor and
review Prompt and Continue tasks against authenticated AI applications (Chrome, Brave, Edge and
Claude Desktop). Everything runs on your own computer: there is **no cloud backend, VPS, or
database server**.

> Source of truth: `SYSTEM_SPECIFICATION.pdf` (Phase 1, v1.0). Later phases implement it; they do
> not redefine it.

## Current phase

**Phase 2 - Development Environment Setup.** This repository currently contains only the
foundation: project skeleton, Python environment, FastAPI app with health endpoints, SQLite /
SQLAlchemy / Alembic foundation, logging, configuration, setup/start scripts, tests and docs.

Not implemented yet (by design): tasks, scheduling, queue, state machine, browser or desktop
automation, file attachment, sleep/wake automation, retries, the real dashboard. See
`docs/PHASE_2_COMPLETION_REPORT.md`.

## Technology stack

| Area | Choice |
| --- | --- |
| Language | Python 3.12 (3.13 allowed) |
| API | FastAPI + Uvicorn, bound to `127.0.0.1` |
| Database | SQLite (WAL, foreign keys on) via SQLAlchemy 2.x, migrations with Alembic |
| Browser automation (later) | Playwright |
| Desktop automation (later) | pywinauto / Windows UI Automation |
| Frontend | Plain HTML / CSS / JavaScript |
| Tests | pytest, pytest-asyncio, httpx |
| Quality | ruff, black, mypy |

## Quick start (Windows)

```powershell
cd C:\Projects\local-ai-task-automation
powershell -ExecutionPolicy Bypass -File scripts\install\setup.ps1
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
# open http://127.0.0.1:8000
```

Full instructions: [`docs/SETUP.md`](docs/SETUP.md). Developer notes:
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md). Problems: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

## Safety rules

The system never asks for, stores or logs passwords, cookies or tokens; never touches your personal
browser profiles; and never bypasses authentication, CAPTCHA or rate limits. The API listens on
localhost only.
