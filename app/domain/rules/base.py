from abc import ABC, abstractmethod
from typing import List
from app.core.uow import IUnitOfWork
from app.domain.entities.anomaly import AnomalyEntity

class DetectionRule(ABC):
    name: str

    @abstractmethod
    def run(self, uow: IUnitOfWork) -> List[AnomalyEntity]:
        ...
