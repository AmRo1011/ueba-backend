from sqlalchemy.orm import Session
from sqlalchemy import select
from app.domain.repositories.base import IAnomalyRepo
from app.domain.entities.anomaly import AnomalyEntity
from app.infra.db.models import Anomaly, AnomalyType

class AnomalyRepo(IAnomalyRepo):
    def __init__(self, db: Session):
        self.db = db

    def resolve_type_id(self, code: str) -> int:
        t = self.db.execute(select(AnomalyType).where(AnomalyType.code == code)).scalar_one_or_none()
        if t: return t.id
        t = AnomalyType(code=code, name=code.replace("_"," ").title())
        self.db.add(t); self.db.flush()
        return t.id

    def add(self, e: AnomalyEntity) -> AnomalyEntity:
        a = Anomaly(
            user_id=e.user_id, anomaly_type_id=e.anomaly_type_id,
            score=e.score, risk=e.risk, confidence=e.confidence,
            status=e.status, evidence_json=e.evidence, detected_at=e.detected_at
        )
        self.db.add(a); self.db.flush()
        e.id = a.id
        return e

    def set_status(self, anomaly_id: int, status: str) -> None:
        self.db.query(Anomaly).filter(Anomaly.id == anomaly_id).update({Anomaly.status: status})
