from datetime import datetime, timezone
from typing import List
from app.domain.rules.base import DetectionRule
from app.core.uow import IUnitOfWork
from app.domain.entities.anomaly import AnomalyEntity

class FailedLoginsRule(DetectionRule):
    name = "failed_logins"

    def run(self, uow: IUnitOfWork) -> List[AnomalyEntity]:
        out: List[AnomalyEntity] = []
        anom_type_id = uow.anomalies.resolve_type_id(self.name)

        for user_id, cnt in uow.logs.failed_login_counts(since_hours=24, min_threshold=3):
            # scoring ??????: ?? 3 ??????? = 0.5 ??? 1.0
            score = min(1.0, (cnt / 3) * 0.5)
            risk  = round(100 * (0.7 * score + 0.3 * 0.6), 2)
            out.append(AnomalyEntity(
                id=None, user_id=user_id, anomaly_type_id=anom_type_id,
                score=score, risk=risk, confidence=0.7, status="open",
                detected_at=datetime.now(timezone.utc),
                evidence={"failed_logins_24h": int(cnt)}
            ))
        return out
