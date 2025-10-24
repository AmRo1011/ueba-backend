from typing import Iterable, List, Tuple, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, case  # << ??? ????? case

from app.domain.repositories.base import ILogRepo
from app.domain.entities.log import LogEntity
from app.infra.db.models import Log, ActivityType

class LogRepo(ILogRepo):
    def __init__(self, db: Session):
        self.db = db

    def resolve_activity_type_id(self, code: str) -> int:
        at = self.db.execute(
            select(ActivityType).where(ActivityType.code == code)
        ).scalar_one_or_none()
        if at:
            return at.id
        at = ActivityType(code=code, name=code.replace("_", " ").title())
        self.db.add(at)
        self.db.flush()
        return at.id

    def bulk_add(self, rows: Iterable[LogEntity]) -> int:
        objs = []
        for r in rows:
            objs.append(Log(
                user_id=r.user_id,
                ts=r.ts,
                activity_type_id=r.activity_type_id,
                source_ip=r.source_ip,
                params_json=r.params,
                hour=r.hour,
                is_weekend=r.is_weekend,
                is_night=r.is_night
            ))
        if objs:
            self.db.bulk_save_objects(objs)
        return len(objs)

    def after_hours_counts(self, open_start: int = 8, open_end: int = 18) -> List[Tuple[int, int]]:
        q = (
            self.db.query(Log.user_id, func.count(Log.id).label("cnt"))
            .filter(or_(Log.hour < open_start, Log.hour > open_end))
            .group_by(Log.user_id)
        )
        return [(int(uid), int(cnt)) for uid, cnt in q.all()]

    def failed_login_counts(self, since_hours: int = 24, min_threshold: int = 3) -> List[Tuple[int, int]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        at_id = self.resolve_activity_type_id("login_failed")
        q = (
            self.db.query(Log.user_id, func.count(Log.id).label("cnt"))
            .filter(and_(Log.activity_type_id == at_id, Log.ts >= cutoff))
            .group_by(Log.user_id)
            .having(func.count(Log.id) >= min_threshold)
        )
        return [(int(uid), int(cnt)) for uid, cnt in q.all()]

    def recent_logins(self, since_hours: int = 48, max_per_user: int = 500) -> List[Tuple[int, datetime, str]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        at_id = self.resolve_activity_type_id("login_success")
        q = (
            self.db.query(Log.user_id, Log.ts, Log.source_ip)
            .filter(and_(Log.activity_type_id == at_id, Log.ts >= cutoff))
            .order_by(Log.user_id.asc(), Log.ts.asc())
        )
        rows = q.all()
        out: List[Tuple[int, datetime, str]] = []
        per: Dict[int, int] = {}
        for uid, ts, ip in rows:
            c = per.get(uid, 0)
            if c < max_per_user:
                out.append((int(uid), ts, ip or ""))
                per[uid] = c + 1
        return out

    def feature_window(self, hours: int = 24) -> Dict[int, Dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        at_login_s = self.resolve_activity_type_id("login_success")
        at_login_f = self.resolve_activity_type_id("login_failed")

        base: Dict[int, Dict] = {}

        #  ?????? case(...) ??? func.case
        login_s_expr = case((Log.activity_type_id == at_login_s, 1), else_=0)
        login_f_expr = case((Log.activity_type_id == at_login_f, 1), else_=0)

        q_counts = (
            self.db.query(
                Log.user_id,
                func.sum(login_s_expr).label("login_success_count"),
                func.sum(login_f_expr).label("login_failed_count"),
                func.count(Log.id).label("total_events"),
            )
            .filter(Log.ts >= cutoff)
            .group_by(Log.user_id)
        )
        for uid, succ, fail, total in q_counts.all():
            base[int(uid)] = {
                "user_id": int(uid),
                "login_success_count": int(succ or 0),
                "login_failed_count": int(fail or 0),
                "total_events": int(total or 0),
            }

        q_ips = (
            self.db.query(Log.user_id, func.count(func.distinct(Log.source_ip)).label("unique_ips_24h"))
            .filter(and_(Log.ts >= cutoff, Log.source_ip.isnot(None)))
            .group_by(Log.user_id)
        )
        for uid, u in q_ips.all():
            rec = base.setdefault(int(uid), {"user_id": int(uid)})
            rec["unique_ips_24h"] = int(u or 0)

        q_after = (
            self.db.query(Log.user_id, func.count(Log.id).label("after_hours_count"))
            .filter(and_(Log.ts >= cutoff, or_(Log.hour < 8, Log.hour > 18)))
            .group_by(Log.user_id)
        )
        for uid, c in q_after.all():
            rec = base.setdefault(int(uid), {"user_id": int(uid)})
            rec["after_hours_count"] = int(c or 0)

        q_last = (
            self.db.query(Log.user_id, func.max(Log.hour))
            .filter(and_(Log.ts >= cutoff, Log.activity_type_id == at_login_s))
            .group_by(Log.user_id)
        )
        for uid, h in q_last.all():
            rec = base.setdefault(int(uid), {"user_id": int(uid)})
            rec["last_login_hour"] = int(h or 0)

        for v in base.values():
            v.setdefault("unique_ips_24h", 0)
            v.setdefault("after_hours_count", 0)
            v.setdefault("last_login_hour", 0)

        return base
