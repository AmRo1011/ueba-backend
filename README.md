# UEBA Backend

User and Entity Behavior Analytics (UEBA) service that detects suspicious user activities. Built with FastAPI and PostgreSQL, it processes activity logs to detect anomalies like impossible travel patterns, after-hours access, and repeated failed logins.

## Architecture at a Glance

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐
│ FastAPI  │ ──► │ Detection   │ ──► │ PostgreSQL   │
│ /api/v1  │     │ Rules+Model │     │ (Supabase)   │
└──────────┘     └─────────────┘     └──────────────┘
```

Core components:
- `app/api/routers/` — FastAPI routes (system, data, detection, anomalies)
- `app/domain/rules/` — Pluggable detection rules
- `app/infra/db/` — SQLAlchemy models and repositories
- `migrations/` — Alembic DB migrations

## Setup & Requirements

Prerequisites:
- Python 3.10+
- PostgreSQL 13+ or Supabase project
- Python packages: FastAPI, SQLAlchemy, Alembic, psycopg2-binary

Install:
```powershell
git clone https://github.com/AmRo1011/ueba-backend
cd ueba-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Required environment variables:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ueba
DB_USER=postgres
DB_PASSWORD=secret

# Security
JWT_SECRET=your-secret-key-here

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000

# Optional
PORT=8001
APP_ENV=dev
```

## Run Locally

Option A - Uvicorn:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

URLs:
- API: http://localhost:8001/api/v1
- Docs: http://localhost:8001/docs
- OpenAPI: http://localhost:8001/openapi.json

## Database & Migrations

Initialize and upgrade:
```powershell
# Set connection string
$env:DB_URL = "postgresql+psycopg2://user:pw@host:port/dbname?sslmode=require"

# Run migrations
alembic -c alembic.ini upgrade head
```

Migration order:
1. Lookups (roles, activity_types, anomaly_types)
2. Users
3. Logs
4. Anomalies + indexes

## Detection Pipeline

Built-in rules:
- **After Hours** — Detects activity outside 8am-6pm
- **Failed Logins** — Flags multiple failed attempts (24h window)
- **Impossible Travel** — Checks login IPs for improbable distances

Rules return anomalies with evidence JSON. Detection service updates user risk scores and anomaly counts.

## Security

- JWT Bearer tokens required for most endpoints
- Role-based access: admin, analyst
- Dev token endpoint (temporary): `POST /api/v1/system/dev-token?uid=demo-user&role=admin`

## API List

System endpoints:
- `GET /api/v1/system/health` — Basic health check
  ```json
  {"success": true, "data": {"status": "healthy"}, "timestamp": "..."}
  ```
- `GET /api/v1/system/status` — DB connection status
  ```json
  {"success": true, "data": {"db": "ok", "version": "PostgreSQL 13.x"}}
  ```

Data ingestion (requires admin/analyst):
- `POST /api/v1/data/upload-logs` — Upload CSV/JSON logs
  ```json
  // Required columns: uid, timestamp, activity_type
  {"success": true, "data": {"inserted": 1000}}
  ```

Detection (admin only):
- `POST /api/v1/detection/run` — Run enabled rules
  ```bash
  # Run specific rules
  curl -X POST "/api/v1/detection/run?enabled=after_hours,failed_logins"
  ```
  ```json
  {"success": true, "data": {"created": 5}}
  ```

Anomalies (admin/analyst):
- `GET /api/v1/anomalies` — List anomalies (status=open|closed)
  ```json
  {
    "success": true,
    "data": {
      "items": [
        {
          "id": 1,
          "uid": "user123",
          "type": "after_hours",
          "score": 0.8,
          "risk": 65.5,
          "status": "open"
        }
      ],
      "count": 1
    }
  }
  ```
- `POST /api/v1/anomalies/{id}/resolve` — Close anomaly

Users (admin/analyst):
- `GET /api/v1/users/top-risk` — List high-risk users
  ```bash
  # Get top 20 users with risk > 50
  curl "/api/v1/users/top-risk?limit=20&min_risk=50"
  ```

## Troubleshooting

1. DB Connection — Check `sslmode=require` in URL if using Supabase
2. Large uploads — CSV/JSON ingestion uses 5000-row buffers
3. Migration fails — Run `alembic stamp head` then retry upgrade
4. CORS error — Add frontend origin to CORS_ORIGINS
5. JWT invalid — Check token format: `Bearer <token>`

## Contributing

1. Branch naming: feature/*, fix/*, docs/*
2. Keep rule computation in repository methods
3. Use Black for formatting
4. Follow existing patterns for new rules

License: TBD

---

**Deprecated Files:** The content of `UEBA_Progress_Report.md` and `progress.md` has been consolidated into this README. Refer to `.github/copilot-instructions.md` for detailed AI agent guidance.
