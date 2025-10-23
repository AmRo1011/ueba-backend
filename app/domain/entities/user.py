from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class UserEntity:
    id: Optional[int]
    uid: str
    username: Optional[str] = None
    email: Optional[str] = None
    role: str = "employee"
    risk_score: float = 0.0
    anomaly_count: int = 0
    created_at: Optional[datetime] = None
