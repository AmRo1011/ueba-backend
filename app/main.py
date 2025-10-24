from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.routers.system import router as system_router
from app.api.routers.data import router as data_router
from app.api.routers.detection import router as detection_router
from app.api.routers.anomalies import router as anomalies_router
from app.api.routers.users import router as users_router

app = FastAPI(title="UEBA API", version="0.1.0")

_cors_env = os.getenv('CORS_ORIGINS', '')
_allowed = [o.strip() for o in _cors_env.split(',') if o.strip()] or ['http://localhost:8080','http://127.0.0.1:8080']

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],  # مهم لـ Authorization
)

app.include_router(system_router,     prefix="/api/v1")
app.include_router(data_router,       prefix="/api/v1")
app.include_router(detection_router,  prefix="/api/v1")
app.include_router(anomalies_router,  prefix="/api/v1")
app.include_router(users_router,      prefix="/api/v1")

