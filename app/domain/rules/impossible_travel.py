from datetime import datetime, timezone
from typing import List, Dict, Tuple
from ipaddress import ip_address, ip_network
from app.domain.rules.base import DetectionRule
from app.core.uow import IUnitOfWork
from app.domain.entities.anomaly import AnomalyEntity
from app.infra.utils.ipgeo import IPGeoResolver

class ImpossibleTravelRule(DetectionRule):
    name = "impossible_travel"

    # ????? ??????: > 900 ??/? ????? ?????? ??????? ????
    SPEED_THRESHOLD_KMPH = 900.0
    # fallback: ???? ??? /24 ?? ??? ?? 30 ?????  ????? ????
    FALLBACK_MINUTES = 30

    def _same24(self, ip1: str, ip2: str) -> bool:
        try:
            n1 = ip_network(ip1 + "/24", strict=False)
            n2 = ip_network(ip2 + "/24", strict=False)
            return n1.network_address == n2.network_address
        except Exception:
            return False

    def run(self, uow: IUnitOfWork) -> List[AnomalyEntity]:
        geo = IPGeoResolver()
        out: List[AnomalyEntity] = []
        anom_type_id = uow.anomalies.resolve_type_id(self.name)

        # ???? ???? ??????? login_success
        rows = uow.logs.recent_logins(since_hours=48, max_per_user=500)

        # ??? per user
        by_user: Dict[int, List[Tuple[datetime, str]]] = {}
        for uid, ts, ip in rows:
            by_user.setdefault(uid, []).append((ts, ip))

        now = datetime.now(timezone.utc)

        for user_id, seq in by_user.items():
            if len(seq) < 2: 
                continue
            # seq ?????? ????? ??????
            prev_ts, prev_ip = seq[0]
            prev_loc = geo.locate(prev_ip)
            for curr_ts, curr_ip in seq[1:]:
                curr_loc = geo.locate(curr_ip)

                flagged = False
                evidence = {"prev_ip": prev_ip, "curr_ip": curr_ip, "prev_ts": prev_ts.isoformat(), "curr_ts": curr_ts.isoformat()}

                if prev_loc and curr_loc:
                    speed = geo.speed_kmph(prev_loc, prev_ts, curr_loc, curr_ts)
                    if speed and speed > self.SPEED_THRESHOLD_KMPH:
                        flagged = True
                        evidence["speed_kmph"] = round(speed, 2)
                        evidence["prev_country"] = prev_loc[2]
                        evidence["curr_country"] = curr_loc[2]
                else:
                    # Fallback: ?????? /24 ???? ???? ?????
                    delta_min = abs((curr_ts - prev_ts).total_seconds())/60.0
                    if curr_ip and prev_ip and (not self._same24(prev_ip, curr_ip)) and delta_min <= self.FALLBACK_MINUTES:
                        flagged = True
                        evidence["delta_minutes"] = int(delta_min)
                        evidence["subnet_jump"] = True

                if flagged:
                    score = 0.8  # ???? ??????
                    risk  = 85.0 # ???? ?????? ???? ????? ????? ????????
                    out.append(AnomalyEntity(
                        id=None, user_id=user_id, anomaly_type_id=anom_type_id,
                        score=score, risk=risk, confidence=0.75, status="open",
                        detected_at=curr_ts, evidence=evidence
                    ))

                prev_ts, prev_ip, prev_loc = curr_ts, curr_ip, curr_loc

        return out
