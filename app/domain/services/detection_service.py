from app.core.uow import IUnitOfWork
from app.domain.rules.registry import get_rules

class DetectionService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def run_all(self, enabled=None) -> int:
        created = 0
        for rule in get_rules(enabled):
            anomalies = rule.run(self.uow)
            for a in anomalies:
                self.uow.anomalies.add(a)
                self.uow.users.bump_user_risk(a.user_id, a.risk)
            self.uow.commit()
            created += len(anomalies)
        return created
