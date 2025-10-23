from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_
from typing import Iterable
from datetime import datetime, timedelta, timezone
from app.domain.repositories.base import ILogRepo
from app.domain.entities.log import LogEntity
from app.infra.db.models import Log, ActivityType

class LogRepo(ILogRepo):
    def __init__(self, db: Session):
        self.db = db

    def resolve_activity_type_id(self, code: str) -> int:
        at = self.db.execute(select(ActivityType).where(ActivityType.code == code)).scalar_one_or_none()
        if at: return at.id
        at = ActivityType(code=code, name=code.replace("_"," ").title())
        self.db.add(at); self.db.flush()
        return at.id

    def bulk_add(self, rows: Iterable[LogEntity]) -> int:
        objs = []
        for r in rows:
            objs.append(Log(
                user_id=r.user_id, ts=r.ts, activity_type_id=r.activity_type_id,
                source_ip=r.source_ip, params_json=r.params, hour=r.hour,
                is_weekend=r.is_weekend, is_night=r.is_night
            ))
        if objs:
            self.db.bulk_save_objects(objs)
        return len(objs)

    def after_hours_counts(self, open_start:int=8, open_end:int=18):
        q = (self.db.query(Log.user_id, func.count(Log.id))
                .filter(or_(Log.hour < open_start, Log.hour > open_end))
                .group_by(Log.user_id))
        return [(uid, cnt) for uid, cnt in q.all()]

    # NEW: failed logins ???? ????? ????? (??????? 24 ????)
    def failed_login_counts(self, since_hours:int=24, min_threshold:int=3):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        # ???? id ???? activity ??? ?????
        at_id = self.resolve_activity_type_id("login_failed")
        q = (self.db.query(Log.user_id, func.count(Log.id).label("cnt"))
                .filter(and_(Log.activity_type_id == at_id, Log.ts >= cutoff))
                .group_by(Log.user_id)
                .having(func.count(Log.id) >= min_threshold))
        return [(uid, cnt) for uid, cnt in q.all()]
