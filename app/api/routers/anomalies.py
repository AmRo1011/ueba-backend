from fastapi import APIRouter, Depends, Query, HTTPException
from app.api.deps import get_uow, require_role
from app.core.responses import ok
from app.infra.db.models import Anomaly, User, AnomalyType

router = APIRouter(prefix="/anomalies", tags=["anomalies"], dependencies=[Depends(require_role("admin","analyst"))])

@router.get("")
def list_anomalies(uow = Depends(get_uow), status: str | None = Query(None, pattern="^(open|closed)$"), limit: int = 50, offset: int = 0):
    q = (uow._session.query(Anomaly, User.uid, AnomalyType.code)
            .join(User, Anomaly.user_id == User.id)
            .join(AnomalyType, Anomaly.anomaly_type_id == AnomalyType.id))
    if status:
        q = q.filter(Anomaly.status == status)
    q = q.order_by(Anomaly.detected_at.desc()).limit(limit).offset(offset)
    items=[]
    for a, uid, at_code in q.all():
        items.append({
            "id": a.id, "uid": uid, "type": at_code, "score": a.score,
            "risk": a.risk, "confidence": a.confidence, "status": a.status,
            "detected_at": a.detected_at, "evidence": a.evidence_json
        })
    return ok({"items": items, "count": len(items)})

@router.post("/{anomaly_id}/resolve")
def resolve_anomaly(anomaly_id: int, uow = Depends(get_uow)):
    a = uow._session.get(Anomaly, anomaly_id)
    if not a: raise HTTPException(404, "Anomaly not found")
    if a.status != "closed":
        a.status = "closed"
        uow.commit()
    return ok({"id": anomaly_id, "status": "closed"})
