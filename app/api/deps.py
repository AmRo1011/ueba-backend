from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, Callable
from app.infra.db.database import get_db
from app.core.uow import IUnitOfWork
from app.infra.db.uow_sqlalchemy import SQLAlchemyUoW
from app.core.security import verify_token
from app.core.auth_supabase import get_current_user

def get_uow(db: Session = Depends(get_db)) -> IUnitOfWork:
    return SQLAlchemyUoW(db)

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload

def require_role(*roles):
    def wrapper(user = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        return user
    return wrapper
