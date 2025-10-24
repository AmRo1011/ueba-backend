import os
from typing import List
from app.core.uow import IUnitOfWork
from app.domain.rules.registry import get_rules
from app.domain.entities.anomaly import AnomalyEntity
from app.domain.services.feature_builder import FeatureBuilder
from app.infra.models.catboost_detector import CatBoostDetector
from app.infra.models.model_registry import pick_insider, pick_ueba

class DetectionService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def _to_entities(self, preds: list[dict], anomaly_type_code: str) -> List[AnomalyEntity]:
        anom_type_id = self.uow.anomalies.resolve_type_id(anomaly_type_code)
        out: List[AnomalyEntity] = []
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for p in preds:
            out.append(AnomalyEntity(
                id=None,
                user_id=int(p["user_id"]),
                anomaly_type_id=anom_type_id,
                score=float(p["score"]),
                risk=float(p["risk"]),
                confidence=float(p.get("confidence", 0.8)),
                status="open",
                detected_at=now,
                evidence=p.get("evidence", {})
            ))
        return out

    def run_all(self, enabled: list[str] | None = None) -> int:
        created = 0
        anomalies: List[AnomalyEntity] = []

        # 1) rules ?????????
        for r in get_rules(enabled):
            anomalies.extend(r.run(self.uow))

        # 2) model-based
        if enabled and any(x.startswith("model_") for x in enabled):
            fb = FeatureBuilder(self.uow)
            rows = fb.build_rows(hours=24)

            for name in enabled:
                if name == "model_ueba":
                    mp = pick_ueba()
                    if mp:
                        det = CatBoostDetector(mp.path)
                        preds = det.infer(rows)
                        anomalies.extend(self._to_entities(preds, anomaly_type_code=mp.name))
                if name == "model_insider":
                    mp = pick_insider()
                    if mp:
                        det = CatBoostDetector(mp.path)
                        preds = det.infer(rows)
                        anomalies.extend(self._to_entities(preds, anomaly_type_code=mp.name))

        # persist
        if anomalies:
            created += self.uow.anomalies.bulk_add(anomalies)
            self.uow.commit()
        return created
