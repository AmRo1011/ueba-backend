from datetime import datetime
from typing import List
from app.domain.rules.base import DetectionRule
from app.core.uow import IUnitOfWork
from app.domain.entities.anomaly import AnomalyEntity

class AfterHoursRule(DetectionRule):
    name = "after_hours"

    def run(self, uow: IUnitOfWork) -> List[AnomalyEntity]:
        out: List[AnomalyEntity] = []
        anom_type_id = uow.anomalies.resolve_type_id(self.name)

        for user_id, cnt in uow.logs.after_hours_counts(open_start=8, open_end=18):
            score = min(1.0, cnt / 10.0)  # ????? ???????
            risk  = round(100 * (0.6*score + 0.4*0.5), 2)
            out.append(AnomalyEntity(
                id=None, user_id=user_id, anomaly_type_id=anom_type_id,
                score=score, risk=risk, confidence=0.6, status="open",
                detected_at=datetime.utcnow(), evidence={"violations": int(cnt)}
            ))
        return out
