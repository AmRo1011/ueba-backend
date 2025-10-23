from abc import ABC, abstractmethod
from app.domain.repositories.base import IUserRepo, ILogRepo, IAnomalyRepo

class IUnitOfWork(ABC):
    users: IUserRepo
    logs: ILogRepo
    anomalies: IAnomalyRepo

    @abstractmethod
    def commit(self) -> None: ...
    @abstractmethod
    def rollback(self) -> None: ...
