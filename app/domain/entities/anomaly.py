from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class AnomalyEntity:
    id: Optional[int]
    user_id: int
    anomaly_type_id: int
    score: float
    risk: float
    confidence: float
    status: str = "open"
    detected_at: datetime = datetime.utcnow()
    evidence: dict | None = None
