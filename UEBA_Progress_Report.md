# UEBA Backend – Progress Report (Up to 2025-10-23)

> This Markdown is ready to drop into your repo (e.g., `docs/PROGRESS.md`).  
> It documents what we built, how it’s structured, how to run and test it, the decisions taken, and what’s next.

---

## Table of Contents

- [Overview](#overview)
- [Architecture (SOLID-oriented)](#architecture-solid-oriented)
- [Project Structure](#project-structure)
- [Environment & Configuration](#environment--configuration)
- [Database Schema & Migrations](#database-schema--migrations)
- [Seeding Lookups](#seeding-lookups)
- [Implemented API Endpoints](#implemented-api-endpoints)
- [Data Ingestion Flow](#data-ingestion-flow)
- [Detection Rules](#detection-rules)
- [Security (JWT + CORS)](#security-jwt--cors)
- [How to Run (Windows/PowerShell)](#how-to-run-windowspowershell)
- [Smoke Tests (curl/PowerShell)](#smoke-tests-curlpowershell)
- [Troubleshooting Log](#troubleshooting-log)
- [Next Steps / Roadmap](#next-steps--roadmap)
- [Appendix: Sample CSV](#appendix-sample-csv)

---

## Overview

- **Goal:** Build a lightweight, explainable UEBA backend: ingest logs → normalize/store → run behavior rules → produce anomalies & risk scores → expose data via APIs for the frontend.
- **Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL (Supabase), Python 3.13.
- **Status:** End-to-end pipeline working:
  - Upload logs (CSV/JSON) → stored in `logs` and `users`.
  - Run detection rules → anomalies generated, user risk updated.
  - List/resolve anomalies and view top-risk users.
  - Basic **JWT auth** (dev token) and **CORS** in place.

---

## Architecture (SOLID-oriented)

**Key design choices aligned with SOLID:**

- **Single Responsibility:**  
  - Repositories per aggregate (`UserRepo`, `LogRepo`, `AnomalyRepo`).  
  - Rules isolated in `domain/rules/*`.  
  - `DetectionService` orchestrates rules only.
- **Open/Closed:**  
  - Add new detection rules by adding a class and registering it in `rules/registry.py` (no changes elsewhere).
- **Liskov Substitution:**  
  - Repos implement minimal interfaces (`IUserRepo`, `ILogRepo`, `IAnomalyRepo`).
- **Interface Segregation:**  
  - Separate small repo interfaces rather than one fat interface.
- **Dependency Inversion:**  
  - App code depends on abstractions (`IUnitOfWork`, repo interfaces). Concrete `SQLAlchemyUoW` and repos injected via `get_uow`.

---

## Project Structure

```
app/
  api/
    deps.py
    routers/
      system.py
      data.py
      detection.py
      anomalies.py
      users.py
  core/
    security.py
    responses.py
    uow.py
  domain/
    entities/
      user.py, log.py, anomaly.py
    repositories/
      base.py
    rules/
      base.py
      after_hours.py
      failed_logins.py
      registry.py
    services/
      detection_service.py
  infra/
    db/
      database.py
      models.py
      seed_lookups.py
      uow_sqlalchemy.py
      repositories/
        user_repo.py
        log_repo.py
        anomaly_repo.py
  main.py
migrations/
alembic.ini
.env
requirements.txt
```

---

## Environment & Configuration

```
APP_ENV=dev
PORT=8001
JWT_SECRET=dev_secret_change_me
DB_HOST=...supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=********
DATABASE_URL=postgresql+psycopg2://postgres:URL_ENCODED_PW@HOST:5432/postgres?sslmode=require
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

---

## Database Schema & Migrations

**Tables (3NF):**
- `roles`
- `activity_types`
- `anomaly_types`
- `users`
- `logs`
- `anomalies`

**Indexes:** optimized for joins and queries.

---

## Seeding Lookups

Use:
```bash
python -c "from app.infra.db.database import SessionLocal; from app.infra.db.seed_lookups import upsert_lookups; db=SessionLocal(); upsert_lookups(db); print('seeded'); db.close()"
```

---

## Implemented API Endpoints

`/api/v1/system`, `/api/v1/data`, `/api/v1/detection`, `/api/v1/anomalies`, `/api/v1/users`  
All unified under consistent response shape.

---

## Data Ingestion Flow

- Supports CSV/JSON.
- Auto-creates users.
- Derives `hour`, normalizes timestamps.
- Bulk-inserts for performance.

---

## Detection Rules

- **After Hours:** detect activities outside working hours.
- **Failed Logins:** detect login_failed spikes.

---

## Security (JWT + CORS)

- Dev JWTs with `/system/dev-token`.
- Role-based access via `require_role(...)`.
- Configurable origins via `.env`.

---

## How to Run (Windows/PowerShell)

```pwsh
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

---

## Smoke Tests (curl/PowerShell)

```pwsh
$tok = (iwr -Method POST "http://localhost:8001/api/v1/system/dev-token?uid=demo&role=admin").Content | ConvertFrom-Json
$Bearer = "Bearer " + $tok.data.access_token
curl.exe -H "Authorization: $Bearer" -F "file=@C:\sample.csv" http://localhost:8001/api/v1/data/upload-logs
iwr -Method POST -Headers @{Authorization=$Bearer} "http://localhost:8001/api/v1/detection/run"
```

---

## Troubleshooting Log

Key issues solved:
- Alembic interpolation errors (URL encoding fix).
- Supabase reset and fresh migration.
- Python-multipart install for file uploads.
- Implemented SQLAlchemyUoW wiring.

---

## Next Steps / Roadmap

1. Add **Impossible Travel Rule**.
2. Integrate **Supabase Auth** (RS256 JWTs).
3. Optimize indexes and queries.
4. Add unit tests and background tasks.
5. Add Prometheus metrics and Celery queue.
