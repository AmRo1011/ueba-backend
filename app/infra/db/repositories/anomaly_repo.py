from __future__ import annotations
from typing import Iterable, Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.domain.repositories.base import IAnomalyRepo
from app.infra.db.models import Anomaly, AnomalyType

# ????? ????????? ????????? ?? AnomalyEntity ??????? ?????? ???
try:
    from app.domain.entities.anomaly import AnomalyEntity  # type: ignore
except Exception:
    AnomalyEntity = object  # fallback

RowType = Union[Dict[str, Any], "AnomalyEntity"]

class AnomalyRepo(IAnomalyRepo):
    def __init__(self, db: Session):
        self.db = db

    # -------- Lookup helpers --------
    def resolve_anomaly_type_id(self, code: str) -> int:
        at = self.db.execute(
            select(AnomalyType).where(AnomalyType.code == code)
        ).scalar_one_or_none()
        if at:
            return at.id
        at = AnomalyType(code=code, name=code.replace("_", " ").title())
        self.db.add(at)
        self.db.flush()
        return at.id

    # ????? ?????? ??? interface
    def resolve_type_id(self, code: str) -> int:
        return self.resolve_anomaly_type_id(code)

    # -------- single add --------
    def add(
        self,
        *,
        user_id: int,
        type_code: str,
        score: float,
        risk: float,
        confidence: float,
        detected_at: Optional[datetime] = None,
        evidence: Optional[dict] = None,
        status: str = "open",
    ) -> int:
        at_id = self.resolve_anomaly_type_id(type_code)
        anom = Anomaly(
            user_id=user_id,
            anomaly_type_id=at_id,
            score=score,
            risk=risk,
            confidence=confidence,
            status=status,
            detected_at=detected_at or datetime.now(timezone.utc),
            evidence_json=evidence or {},
        )
        self.db.add(anom)
        self.db.flush()
        return anom.id

    # -------- coercion helper --------
    def _coerce_row(self, r: RowType) -> Dict[str, Any]:
        """
        ????? ???? dict ?? AnomalyEntity ??? dict ????? ?????.
        ???????? ???????:
          user_id, anomaly_type, score, risk, confidence, status, detected_at, evidence
        """
        if isinstance(r, dict):
            return {
                "user_id": r.get("user_id"),
                "anomaly_type": r.get("anomaly_type") or r.get("type") or "model_ueba",
                "score": r.get("score", 0.0),
                "risk": r.get("risk", 0.0),
                "confidence": r.get("confidence", 0.0),
                "status": r.get("status", "open"),
                "detected_at": r.get("detected_at"),
                "evidence": r.get("evidence") or r.get("evidence_json") or {},
            }
        # ???? ???? ?? ???? ?????
        # ????? ????? ?? ??? Entity: user_id, type_code|anomaly_type|type, score, risk, confidence, status, detected_at, evidence
        get = lambda obj, *names, default=None: next((getattr(obj, n) for n in names if hasattr(obj, n)), default)
        return {
            "user_id": int(get(r, "user_id", default=0)),
            "anomaly_type": get(r, "type_code", "anomaly_type", "type", default="model_ueba"),
            "score": float(get(r, "score", default=0.0) or 0.0),
            "risk": float(get(r, "risk", default=0.0) or 0.0),
            "confidence": float(get(r, "confidence", default=0.0) or 0.0),
            "status": str(get(r, "status", default="open") or "open"),
            "detected_at": get(r, "detected_at", default=None),
            "evidence": get(r, "evidence", "evidence_json", default={}) or {},
        }

    # -------- bulk add --------
    def bulk_add(self, rows: Iterable[RowType]) -> int:
        objs: List[Anomaly] = []
        now = datetime.now(timezone.utc)
        type_cache: Dict[str, int] = {}

        for raw in rows:
            r = self._coerce_row(raw)
            uid = int(r["user_id"])
            tcode = str(r.get("anomaly_type") or "model_ueba")

            if tcode not in type_cache:
                type_cache[tcode] = self.resolve_anomaly_type_id(tcode)

            objs.append(
                Anomaly(
                    user_id=uid,
                    anomaly_type_id=type_cache[tcode],
                    score=float(r.get("score", 0.0)),
                    risk=float(r.get("risk", 0.0)),
                    confidence=float(r.get("confidence", 0.0)),
                    status=str(r.get("status", "open")),
                    detected_at=r.get("detected_at") or now,
                    evidence_json=r.get("evidence") or {},
                )
            )

        if objs:
            self.db.bulk_save_objects(objs)
        return len(objs)

    # -------- status update --------
    def set_status(self, anomaly_id: int, status: str = "closed") -> bool:
        res = self.db.execute(
            update(Anomaly)
            .where(Anomaly.id == anomaly_id)
            .values(status=status)
        )
        self.db.flush()
        return (res.rowcount or 0) > 0
