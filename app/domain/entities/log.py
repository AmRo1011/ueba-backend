from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

@dataclass
class LogEntity:
    id: Optional[int]
    user_id: int
    ts: datetime
    activity_type_id: int
    source_ip: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    hour: Optional[int] = None
    is_weekend: Optional[bool] = None
    is_night: Optional[bool] = None
