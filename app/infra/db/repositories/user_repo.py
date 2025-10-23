from sqlalchemy.orm import Session
from sqlalchemy import select
from app.domain.repositories.base import IUserRepo
from app.domain.entities.user import UserEntity
from app.infra.db.models import User, Role

class UserRepo(IUserRepo):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> UserEntity | None:
        u = self.db.get(User, id)
        if not u: return None
        return UserEntity(id=u.id, uid=u.uid, username=u.username, email=u.email,
                          role=u.role.code if u.role else "employee",
                          risk_score=u.risk_score, anomaly_count=u.anomaly_count,
                          created_at=u.created_at)

    def get_by_uid(self, uid: str) -> UserEntity | None:
        u = self.db.execute(select(User).where(User.uid == uid)).scalar_one_or_none()
        if not u: return None
        return UserEntity(id=u.id, uid=u.uid, username=u.username, email=u.email,
                          role=u.role.code if u.role else "employee",
                          risk_score=u.risk_score, anomaly_count=u.anomaly_count,
                          created_at=u.created_at)

    def add(self, e: UserEntity) -> UserEntity:
        role = self.db.execute(select(Role).where(Role.code == (e.role or "employee"))).scalar_one_or_none()
        u = User(uid=e.uid, username=e.username, email=e.email, role=role)
        self.db.add(u); self.db.flush()
        e.id = u.id
        return e

    def update(self, e: UserEntity) -> None:
        self.db.query(User).filter(User.id == e.id).update({
            User.username: e.username,
            User.email: e.email,
            User.risk_score: e.risk_score,
            User.anomaly_count: e.anomaly_count,
        })

    def bump_user_risk(self, user_id: int, risk: float):
        u = self.db.get(User, user_id)
        if not u: return
        if risk > (u.risk_score or 0):
            u.risk_score = risk
        u.anomaly_count = (u.anomaly_count or 0) + 1

    def top_by_risk(self, limit:int=100, min_risk:float=0):
        rows = (self.db.query(User)
                  .filter(User.risk_score >= min_risk)
                  .order_by(User.risk_score.desc())
                  .limit(limit).all())
        out=[]
        for u in rows:
            out.append(UserEntity(
                id=u.id, uid=u.uid, username=u.username, email=u.email,
                role=u.role.code if u.role else "employee",
                risk_score=u.risk_score, anomaly_count=u.anomaly_count,
                created_at=u.created_at
            ))
        return out
