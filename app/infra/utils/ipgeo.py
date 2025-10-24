import os, math
from typing import Optional, Tuple

class IPGeoResolver:
    def __init__(self):
        self.db_path = os.getenv("GEOIP_DB_PATH")
        self.client = None
        if self.db_path:
            try:
                import geoip2.database  # type: ignore
                self.client = geoip2.database.Reader(self.db_path)
            except Exception:
                self.client = None

    def _haversine(self, p1: Tuple[float,float], p2: Tuple[float,float]) -> float:
        # km
        R = 6371.0
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return 2*R*math.asin(math.sqrt(a))

    def locate(self, ip: str) -> Optional[Tuple[float,float,str]]:
        if not ip:
            return None
        if self.client:
            try:
                r = self.client.city(ip)
                if r and r.location and r.location.latitude and r.location.longitude:
                    return (float(r.location.latitude), float(r.location.longitude), (r.country.iso_code or ""))
            except Exception:
                return None
        # no DB ? return None; rule ????? ?? fallback
        return None

    def speed_kmph(self, p1, t1, p2, t2) -> Optional[float]:
        # p = (lat, lon, country)
        if not p1 or not p2:
            return None
        dist = self._haversine((p1[0],p1[1]), (p2[0],p2[1]))
        delta_h = abs((t2 - t1).total_seconds()) / 3600.0
        if delta_h == 0:
            return None
        return dist / delta_h
