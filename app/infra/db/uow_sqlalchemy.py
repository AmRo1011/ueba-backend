from contextlib import AbstractContextManager
from sqlalchemy.orm import Session
from app.core.uow import IUnitOfWork
from app.infra.db.repositories.user_repo import UserRepo
from app.infra.db.repositories.log_repo import LogRepo
from app.infra.db.repositories.anomaly_repo import AnomalyRepo

class SQLAlchemyUoW(IUnitOfWork, AbstractContextManager):
    def __init__(self, session: Session):
        self._session = session
        self.users = UserRepo(session)
        self.logs = LogRepo(session)
        self.anomalies = AnomalyRepo(session)

    def __exit__(self, exc_type, exc, tb):
        if exc: self.rollback()
        else: self.commit()
        self._session.close()

    def commit(self): self._session.commit()
    def rollback(self): self._session.rollback()
