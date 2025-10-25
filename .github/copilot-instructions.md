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
# Copilot guidance for this repository

This file helps AI coding agents be productive quickly in the UEBA backend. It now contains both high-level guidance and concrete implementation details discovered while inspecting the codebase.

High-level architecture
- FastAPI app serving under `/api/v1` (see `app/main.py`). Routers live in `app/api/routers/` and use dependencies from `app/api/deps.py`.
- SQLAlchemy ORM with a session-based Unit-of-Work (UoW) pattern: `SQLAlchemyUoW` (in `app/infra/db/uow_sqlalchemy.py`) composes repository classes (`app/infra/db/repositories/*`) and exposes them as `uow.users`, `uow.logs`, `uow.anomalies`.
- Detection rules are plug-ins: rules are classes under `app/domain/rules/` and registered by `app/domain/rules/registry.py`. `DetectionService.run_all()` iterates rules and persists anomalies returned by them.

Important concrete files to read (examples and single-source-of-truth)
- `app/main.py` — app entry, CORS middleware, router wiring.
- `app/core/config.py` — environment configuration. DATABASE_URL uses `quote_plus` and forces `sslmode=require`.
- `app/core/responses.py` — every endpoint wraps responses using `ok(data)` which returns {"success", "message", "data", "timestamp"}.
- `app/api/deps.py` — DI helpers: `get_db`, `get_uow`, `get_current_user` (JWT bearer expectation), and `require_role(...)` to gate endpoints.
- `app/infra/db/database.py` — SQLAlchemy engine and `SessionLocal`, `get_db()` generator used by routes.
- `app/infra/db/models.py` — canonical DB schema. Use column names here (e.g., `User.uid`, `Anomaly.status`) when writing raw queries.
- `app/infra/db/uow_sqlalchemy.py` — constructs `UserRepo`, `LogRepo`, `AnomalyRepo` and provides `commit` / `rollback` and context manager behavior.
- `app/infra/db/repositories/*.py` — repository methods and signatures (see below for exact names).
- `app/domain/rules/*` — each rule implements `run(uow)` and returns anomalies (see `after_hours.py`, `failed_logins.py`).

Repository method signatures & behaviors (use these directly)
- UserRepo (`app/infra/db/repositories/user_repo.py`)
  - get_by_id(id) -> UserEntity | None
  - get_by_uid(uid) -> UserEntity | None
  - add(UserEntity) -> UserEntity (sets e.id)
  - update(UserEntity) -> None
  - bump_user_risk(user_id, risk) -> None  (updates risk_score if higher and increments anomaly_count)
  - top_by_risk(limit=100, min_risk=0) -> list[UserEntity]

- LogRepo (`app/infra/db/repositories/log_repo.py`)
  - resolve_activity_type_id(code) -> int (creates lookup if missing)
  - bulk_add(rows: Iterable[LogEntity]) -> int (uses bulk_save_objects)
  - after_hours_counts(open_start=8, open_end=18) -> List[(user_id, count)]
  - failed_login_counts(since_hours=24, min_threshold=3) -> List[(user_id, count)]
  - recent_logins(since_hours=48, max_per_user=500) -> List[(user_id, ts, ip)]
  - feature_window(hours=24) -> Dict[user_id, features...] (multiple aggregated features)

- AnomalyRepo (`app/infra/db/repositories/anomaly_repo.py`)
  - resolve_anomaly_type_id(code) -> int (creates lookup if missing)
  - resolve_type_id(code) -> int (alias)
  - add(user_id=..., type_code=..., score=..., risk=..., confidence=..., detected_at=None, evidence=None, status='open') -> int (returns anomaly id)
  - bulk_add(rows: Iterable[dict|AnomalyEntity]) -> int (accepts dict or entity-like objects and writes many anomalies)
  - set_status(anomaly_id, status='closed') -> bool

Key patterns and gotchas (practical)
- Response wrapper: Always use `ok(data)` or match its shape when returning JSON. See `app/core/responses.py`.
- Auth: `app/api/deps.get_current_user` expects an Authorization header with `Bearer <token>` and uses `app/core/security.verify_token()` to decode. Tokens created by `app/core/security.create_token()` (HS256, shared secret from `JWT_SECRET`). Many routes also use `require_role('admin','analyst')` to restrict access.
- Adding detection rules: rules should implement `run(uow)` and return a list of anomaly objects. The codebase uses an `AnomalyEntity` dataclass in many rules, but `AnomalyRepo.bulk_add()` accepts dicts too. Note: `DetectionService.run_all()` in `app/domain/services/detection_service.py` calls `uow.anomalies.add(a)` for each anomaly returned by a rule — pay attention to the repo `add()` signature which expects keyword arguments. If you change rule return types, ensure compatibility with `uow.anomalies.add` or change `DetectionService` to use `uow.anomalies.bulk_add()` or adapt via a small coercion helper.
- Logs ingestion: `app/api/routers/data.py` accepts CSV or JSON arrays. Required columns: `uid`, `timestamp`, `activity_type`. The endpoint will create a `User` automatically if `uid` is unknown (via `uow.users.add(UserEntity(...))`). Keep the CSV/JSON parsing behavior intact (the route normalizes keys to lowercase and converts timestamps with a small normalization step).
- Bulk operations: `bulk_add` is used for performance. For logs, batches of 5000 are used before flushing. Preserve batching when adding large-volume changes.

Running, dev, and migrations (commands and tips)
- Set env vars (or `.env` file) for DB and secrets. Important ones: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `CORS_ORIGINS`.
- Create virtualenv and install:
  - python -m venv .venv
  - .\\.venv\\Scripts\\Activate.ps1
  - pip install -r requirements.txt
- Run dev server:
  - uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
- Run alembic migrations (project root):
  - set DB_URL="postgresql+psycopg2://user:pw@host:port/dbname"; alembic -c alembic.ini upgrade head
  - alembic.ini uses `sqlalchemy.url = %(DB_URL)s` — set the environment variable appropriately in your shell or env.

Where to make safe changes and small helpers to add
- Adding a new detection rule: implement `run(uow)` under `app/domain/rules/`, register in `registry.py`.
- If you add endpoints that mutate DB, prefer `Depends(get_uow)` and call `uow.commit()` after mutations.
- For read-only endpoints that only need simple queries, `db: Session = Depends(get_db)` is acceptable.

Search anchors (quick grep targets)
- `uow.logs.bulk_add` — for ingestion
- `DetectionService.run_all` — orchestrates rules
- `app/api/routers/data.py` — CSV/JSON ingestion logic
- `app/infra/db/repositories/*` — concrete repository behavior

Known limitations & TODOs discovered during analysis
- Tests: There are no unit tests in the inspected files. Add unit tests around `LogRepo.feature_window`, rule logic, and `DetectionService` orchestration.
- Inconsistency risk: `DetectionService.run_all()` calls `uow.anomalies.add(a)` while `AnomalyRepo.add()` is keyword-only. Review and standardize the anomaly add contract (either always produce dicts or change `DetectionService` to call `uow.anomalies.bulk_add()` with a one-item list).

If you'd like I can expand this file with: exact dataclass fields (UserEntity/LogEntity/AnomalyEntity), example snippets for adding a rule, or add a small test harness that runs `DetectionService` against in-memory SQLite for quick integration tests.
