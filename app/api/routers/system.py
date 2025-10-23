from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.infra.db.database import get_db
from app.core.responses import ok

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health")
def health():
    return ok({"status": "healthy"})

@router.get("/status")
def status(db: Session = Depends(get_db)):
    try:
        version = db.execute(text("select version();")).scalar()
        return ok({"db": "ok", "version": version})
    except Exception as e:
        return ok({"db": "error", "reason": str(e)[:200]})

@router.post("/dev-token")
def dev_token(uid: str = "demo-user", role: str = "admin"):
    from app.core.security import create_token
    return ok({"access_token": create_token(sub=uid, role=role), "token_type": "bearer"})
