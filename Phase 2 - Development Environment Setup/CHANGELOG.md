# Changelog

## 0.2.0 - Phase 2: Development environment setup
- Project skeleton matching the Phase 1 specification layout.
- Pinned dependencies (`requirements.txt`, `requirements-dev.txt`) and `pyproject.toml`.
- FastAPI foundation: `GET /api/v1/health`, `/health/database`, `/health/environment`,
  `/system/info`; consistent error shape and request IDs.
- SQLite foundation (foreign keys, WAL, busy timeout), SQLAlchemy base, Alembic (no revisions yet;
  version table `schema_migrations`).
- Structured JSON logging with redaction; configuration via `.env`.
- Windows setup/start scripts; minimal status page; pytest suite.

## 0.1.0 - Phase 1: Requirement and system specification
- `SYSTEM_SPECIFICATION.pdf` v1.0 (document only; no code).
