from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

class ThreatType(BaseModel):
    type: str
    label: str
    count: int
    percentage: float

class ThreatDistributionResp(BaseModel):
    threat_types: List[ThreatType]
    total_threats: int

class DeptRisk(BaseModel):
    department_id: str
    department_name: str
    average_risk_score: float
    user_count: int
    high_risk_users: int

class RiskByDeptResp(BaseModel):
    departments: List[DeptRisk]

@router.get("/threat-distribution", response_model=ThreatDistributionResp)
def threat_distribution():
    return {
        "threat_types": [
            {"type": "data_exfiltration", "label": "Data Exfiltration", "count": 23, "percentage": 35},
            {"type": "privilege_abuse", "label": "Privilege Abuse", "count": 18, "percentage": 28},
            {"type": "geo_anomaly", "label": "Geo Anomaly", "count": 14, "percentage": 22},
            {"type": "off_hours", "label": "Off-hours Activity", "count": 11, "percentage": 15},
        ],
        "total_threats": 66,
    }

@router.get("/risk-by-department", response_model=RiskByDeptResp)
def risk_by_department():
    return {
        "departments": [
            {"department_id": "dept_fin", "department_name": "Finance", "average_risk_score": 92, "user_count": 45, "high_risk_users": 3},
            {"department_id": "dept_it", "department_name": "IT Ops", "average_risk_score": 70, "user_count": 60, "high_risk_users": 5},
            {"department_id": "dept_hr", "department_name": "HR", "average_risk_score": 58, "user_count": 22, "high_risk_users": 1},
        ]
    }
