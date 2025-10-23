from fastapi import APIRouter, Depends, Query
from app.api.deps import get_uow, require_role
from app.core.responses import ok

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_role("admin","analyst"))])

@router.get("/top-risk")
def top_risk(uow = Depends(get_uow), limit:int=20, min_risk:float=0):
    users = uow.users.top_by_risk(limit=limit, min_risk=min_risk)
    items = [{"id":u.id,"uid":u.uid,"username":u.username,"risk_score":u.risk_score,"anomaly_count":u.anomaly_count} for u in users]
    return ok({"items": items})
