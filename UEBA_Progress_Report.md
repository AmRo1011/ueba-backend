# UEBA Backend – Progress Report (Up to 2025-10-24)

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
- [Machine Learning Detection](#machine-learning-detection)
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
- **Status:** Core pipeline is stable and enhanced with major new features:
  - **Impossible Travel Rule** and **ML-based detection** now operational.
  - **Supabase Auth (RS256)** integrated for production-ready security.
  - All original features (log ingestion, rule execution, anomaly management) remain functional.

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
    auth_supabase.py
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
      impossible_travel.py
      registry.py
    services/
      detection_service.py
      feature_builder.py
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
    models/
      catboost_detector.py
      model_registry.py
    utils/
      ipgeo.py
  main.py
models/
  insider_catboost.cbm
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

- **After Hours:** Detects activities outside of standard working hours.
- **Failed Logins:** Identifies spikes in `login_failed` events for a user.
- **Impossible Travel:** Flags user activity from geographically distant locations in an impossibly short time frame.

---

## Machine Learning Detection

- **CatBoost Model:** A new ML-based detection capability has been integrated to identify complex patterns indicative of insider threats.
- **Workflow:**
  1.  `FeatureBuilder` service transforms raw logs into numerical feature vectors.
  2.  `CatBoostDetector` loads the pre-trained model (`insider_catboost.cbm`).
  3.  The model predicts an anomaly score for the user's activity.

---

## Security (JWT + CORS)

- **Supabase Auth:** Integrated for production-ready security. The system now validates RS256 JWTs issued by Supabase, replacing the previous dev-only tokens.
- **Role-Based Access:** Continues to use `require_role(...)` for fine-grained access control.
- **CORS:** Origins remain configurable via `.env`.

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

1. **DONE:** Add **Impossible Travel Rule**.
2. **DONE:** Integrate **Supabase Auth** (RS256 JWTs).
3. **NEW:** Integrate **ML Model** for advanced anomaly detection.
4. Optimize database indexes and high-traffic queries.
5. Implement unit and integration tests for critical services.
6. Introduce background tasks (e.g., Celery) for non-blocking detection runs.
7. Add Prometheus metrics for monitoring API performance and system health.
