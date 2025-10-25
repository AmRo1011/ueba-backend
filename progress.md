# Project progress & deep dive — UEBA backend

This document explains the codebase structure, why things are organised as they are, and describes each small part so AI agents and contributors can move quickly.

## One-line summary
FastAPI service exposing a UEBA (user behavior analytics) API; PostgreSQL via SQLAlchemy; detection rules as pluggable modules that compute and persist anomalies.

## Top-level layout
- `app/` — source code.
  - `api/routers/` — FastAPI routes (system, data ingestion, detection operations, anomalies, users).
  - `core/` — config, responses, security, UoW interface.
  - `domain/` — business logic: `entities` (dataclasses), `repositories` (interfaces), `rules` (detection logic), `services` (DetectionService orchestration).
  - `infra/db/` — SQLAlchemy models, engine/session, concrete repository implementations, UoW implementation.
- `migrations/` — Alembic migration scripts; initial schema in `migrations/versions/6cf6e8c09ea2_init_schema_3nf.py`.
- `requirements.txt` — pinned packages used by the project.

## Key dataflows
1. Ingest logs: client uploads CSV or JSON array -> `/data/upload-logs` -> parse rows -> ensure `User` exists (uow.users.get_by_uid / add) -> resolve `ActivityType` (uow.logs.resolve_activity_type_id) -> buffer -> uow.logs.bulk_add(buffer) -> uow.commit().
2. Run detection: admin calls `/detection/run` -> `DetectionService.run_all(uow)` iterates rules from `registry.get_rules()` -> each rule calls repo helpers (e.g., `uow.logs.after_hours_counts`) -> rules return anomalies -> detection service persists anomalies and calls `uow.users.bump_user_risk` -> commit per-rule.
3. Query anomalies/users: read endpoints use `get_uow` or `get_db` for queries; sometimes queries use `uow._session` for more advanced joins.

## Important files & responsibilities (per-file)
- `app/main.py` — wires routes and CORS origins. Keep port/origins in `app/core/config.py`.
- `app/core/config.py` — builds `DATABASE_URL` with URL-encoding for credentials and forces `sslmode=require`. Use `.env` values.
- `app/core/responses.py` — `ok(data)` wrapper: responses always use {success, message, data, timestamp}. Tests and docs should reflect that wrapper.
- `app/core/security.py` — HS256 JWT create/verify helpers (`create_token`, `verify_token`). Secret from `JWT_SECRET`.
- `app/api/deps.py` — `get_db`, `get_uow`, `get_current_user` (expects `Authorization: Bearer <token>`), `require_role(...)` which raises 403 if role not allowed.
- `app/api/routers/data.py` — ingestion: CSV or JSON arrays supported; keys lowercased; required: `uid`, `timestamp`, `activity_type`. Creates users automatically when unknown.
- `app/api/routers/anomalies.py` — example of direct session usage for joins: `uow._session.query(Anomaly, User.uid, AnomalyType.code)`.
- `app/infra/db/database.py` — SQLAlchemy engine config. `SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)`; `get_db` yields and closes sessions.
- `app/infra/db/models.py` — authoritative schema. Use names and indexes here when composing raw queries.
- `app/infra/db/uow_sqlalchemy.py` — `SQLAlchemyUoW(session)` constructs repos and implements `commit`, `rollback`, and context manager semantics (`__exit__` commits unless exception).
- `app/infra/db/repositories/*.py` — concrete DB APIs; prefer these over ad-hoc session queries.
- `app/domain/rules/*` — detection rules (AfterHours, FailedLogins, ImpossibleTravel). Rules call repo aggregation helpers and return anomalies.

## Data model quick reference
- Users: `users(uid, username, email, role_id, risk_score, anomaly_count)` — `User.uid` is unique identifier used across ingestion.
- Logs: `logs(user_id, ts, activity_type_id, source_ip, params_json, hour, is_weekend, is_night)` — large table optimized for bulk ingestion.
- Anomalies: `anomalies(user_id, anomaly_type_id, score, risk, confidence, status, detected_at, evidence_json)`.

## Repositories & contracts (exact names for code edits)
- `UserRepo`: `get_by_id`, `get_by_uid`, `add`, `update`, `bump_user_risk`, `top_by_risk`.
- `LogRepo`: `resolve_activity_type_id`, `bulk_add`, `after_hours_counts`, `failed_login_counts`, `recent_logins`, `feature_window`.
- `AnomalyRepo`: `resolve_anomaly_type_id`, `resolve_type_id`, `add` (keyword-only signature), `bulk_add`, `set_status`.

## Rules: what they expect and return
- Rules implement `run(self, uow: IUnitOfWork) -> List[AnomalyEntity]`.
- The repository `AnomalyRepo.bulk_add()` accepts dicts or entity-like objects, but `AnomalyRepo.add()` expects keyword-only args. The engine `DetectionService.run_all()` currently calls `uow.anomalies.add(a)` for each anomaly returned by rules — verify the anomaly object shape when adding rules (either return dicts compatible with `add` or adjust `DetectionService` to call `bulk_add`).

## Running and debugging locally
1. Create and activate venv (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2. Start server:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
3. Migrations (example; set DB_URL first):
```powershell
set DB_URL="postgresql+psycopg2://user:pw@host:port/dbname"; alembic -c alembic.ini upgrade head
```
4. Quick dev token (dev only): `POST /api/v1/system/dev-token?uid=demo-user&role=admin` returns a JWT created by `create_token`.

## Observed quirks & recommended fixes
- Inconsistency: `DetectionService.run_all()` adds anomalies by calling `uow.anomalies.add(a)` while `AnomalyRepo.add()` requires keyword args. Action: either have rules return dicts matching `add(**dict)` or change `DetectionService` to call `uow.anomalies.bulk_add([a])` or add a small coercer that converts an `AnomalyEntity` into keyword args for `add()`.
- Tests: add unit tests around `LogRepo.feature_window`, `after_hours_counts`, `failed_login_counts`, and a small integration test for `DetectionService` using an in-memory SQLite DB (note: some Postgres-specific features may behave differently).

## PR checklist suggestions for maintainers
- Run migrations locally (alembic upgrade head).
- Smoke-test ingestion: POST /api/v1/data/upload-logs with a small CSV.
- Run DetectionService with a small dataset and confirm anomalies persisted and `users.risk_score` updated.
- Linting / types: use `ruff`/`mypy` if added; ensure repository signatures unchanged.

## Next improvements I can implement for you
- Generate an OpenAPI spec (already added at `docs/api_contract.yaml`) and integrate it with FastAPI docs.
- Add a small test harness that seeds a temporary DB, ingests a few logs, runs detection, and asserts anomalies.
- Fix the DetectionService <-> AnomalyRepo contract mismatch by adding a coercion adapter.

If you want I will implement any of the "Next improvements" above. Otherwise tell me any section you want expanded and I'll iterate.
