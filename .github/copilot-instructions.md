# Copilot guidance for this repository

This file helps AI coding agents be productive quickly in the UEBA backend.

High-level summary
- FastAPI app exposing routes under `/api/v1` (see `app/main.py`).
- SQLAlchemy ORM + session-based Unit-of-Work (UoW) pattern behind repositories (`app/infra/db/uow_sqlalchemy.py`, `app/infra/db/repositories`).
- Detection rules are plug-in style: rules are registered in `app/domain/rules/registry.py` and executed by `app/domain/services/detection_service.py`.

Key files to reference (use these for examples and patterns)
- `app/main.py` — app entry, middleware, router wiring.
- `app/core/config.py` — environment-driven config. DATABASE_URL is built here (note: `quote_plus` used for credentials and `sslmode=require`).
- `app/infra/db/database.py` — SQLAlchemy `engine`, `SessionLocal`, and `get_db()` generator.
- `app/infra/db/models.py` — authoritative DB schema and column names (use these names in queries: e.g. `User.uid`, `Anomaly.status`).
- `app/infra/db/uow_sqlalchemy.py` — how UoW composes repos and manages commit/rollback and session lifecycle.
- `app/domain/rules/*` and `app/domain/rules/registry.py` — how rules are discovered and invoked. Rules return Anomaly entities that the UoW persists.
- `app/api/routers/*.py` — route-level patterns; many use `get_uow` dependency (from `app/api/deps.py`) and sometimes use `uow._session` for ad-hoc queries.

Concrete patterns and pitfalls for code edits
- Repositories vs direct session usage: prefer repository APIs on `uow` (e.g. `uow.users.get_by_uid`, `uow.logs.bulk_add`) but note some routers use `uow._session.query(...)` directly for joined queries (see `app/api/routers/anomalies.py`).
- UoW lifecycle: SQLAlchemyUoW implements context manager; some code expects `uow.commit()` calls after mutating repositories (see `DetectionService.run_all`).
- Large data ingestion: `app/api/routers/data.py` buffers log rows (5000) and calls `uow.logs.bulk_add(buffer)`; preserve the buffered/batch approach when modifying ingestion logic.
- Timestamp parsing: `data.upload_logs` uses ISO parsing with minor normalization (`replace(' ', 'T')` and handling trailing `Z`). Keep compatible parsing when extending ingestion.
- Security/roles: endpoints rely on `app/api/deps.require_role(...)` to gate admin/analyst operations (see routers' `dependencies=[Depends(require_role(...))]`).

Running, dev and migrations (what I discovered)
- Environment: `.env` + `app/core/config.py` (`dotenv` is used if available). Important vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `CORS_ORIGINS`.
- Start dev server (common): run the FastAPI ASGI server (uvicorn) pointing at `app.main:app`. Example (shell):
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
- Migrations: Alembic present (`alembic.ini`, `migrations/`). Use `alembic` commands from project root (ensure virtualenv/requirements installed).

Examples agents should follow when editing/adding features
- To add a new detection rule:
  - Create rule under `app/domain/rules/` implementing a `run(uow)` function returning Anomaly entities.
  - Register it in `app/domain/rules/registry.py` so `get_rules()` will find it.
  - Tests/usage: `DetectionService.run_all()` iterates `get_rules()` and persists anomalies via `uow.anomalies.add(...); uow.users.bump_user_risk(...)`.
- To add an API that needs DB access:
  - Use `Depends(get_uow)` from `app/api/deps.py` if the endpoint mutates data and needs repository APIs.
  - For read-only simple operations, you may inject `db: Session = Depends(get_db)` from `app/infra/db/database.py`.

Searchable code idioms (good anchors for edits)
- Bulk ingest: `uow.logs.bulk_add(buffer)` in `app/api/routers/data.py`.
- Rule discovery: `app/domain/rules/registry.py` + `get_rules(enabled)`.
- Direct SQLAlchemy query in route: `uow._session.query(Anomaly, User.uid, AnomalyType.code)` in `app/api/routers/anomalies.py`.

Limitations / things not discovered in code
- No unit tests found in inspected files — be conservative when changing public behavior and run the server locally to smoke-test routes.
- External integrations beyond Postgres are not present; assume only the DB and HTTP API are required.

If anything in this file is unclear or you want deeper examples (e.g. specific repo method signatures, or how tokens are created in `app/core/security.py`), tell me which area to expand and I'll add short examples.
