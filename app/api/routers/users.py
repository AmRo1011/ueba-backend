from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class Department(BaseModel):
    id: str
    name: str

class Role(BaseModel):
    id: str
    title: str

class LastLogin(BaseModel):
    timestamp: str
    relative: str

class Location(BaseModel):
    city: str
    country: str
    is_suspicious: bool = False

class Device(BaseModel):
    type: str
    os: str
    browser: str

class Anoms(BaseModel):
    today: int
    this_week: int

class UserOut(BaseModel):
    user_id: str
    username: str
    full_name: str
    email: Optional[str] = None
    department: Department
    role: Role
    status: Literal["normal", "investigating", "high_risk"]
    risk_score: int
    last_login: LastLogin
    location: Location
    device: Device
    anomalies: Anoms

class Pagination(BaseModel):
    page: int
    per_page: int
    total_pages: int
    total_count: int

class UsersResp(BaseModel):
    users: List[UserOut]
    pagination: Pagination
    filters_applied: Dict[str, str]

class UsersStatsResp(BaseModel):
    total_users: int
    by_status: Dict[str, int]

_MOCK_USERS: List[UserOut] = [
    UserOut(
        user_id="usr_1",
        username="j.anderson",
        full_name="Jane Anderson",
        email="j.anderson@example.com",
        department=Department(id="dept_fin", name="Finance"),
        role=Role(id="role_sa", title="Senior Analyst"),
        status="high_risk",
        risk_score=92,
        last_login=LastLogin(timestamp="2025-10-24T15:45:00Z", relative="2 min ago"),
        location=Location(city="Unknown", country="Unknown", is_suspicious=True),
        device=Device(type="desktop", os="Windows 11", browser="Chrome"),
        anomalies=Anoms(today=3, this_week=8),
    ),
    UserOut(
        user_id="usr_2",
        username="m.chen",
        full_name="Michael Chen",
        email="m.chen@example.com",
        department=Department(id="dept_it", name="IT Operations"),
        role=Role(id="role_sys", title="Systems Admin"),
        status="investigating",
        risk_score=87,
        last_login=LastLogin(timestamp="2025-10-24T15:30:00Z", relative="15 min ago"),
        location=Location(city="New York", country="US", is_suspicious=False),
        device=Device(type="laptop", os="macOS", browser="Safari"),
        anomalies=Anoms(today=2, this_week=6),
    ),
    UserOut(
        user_id="usr_3",
        username="s.rodriguez",
        full_name="Sarah Rodriguez",
        email="s.rodriguez@example.com",
        department=Department(id="dept_hr", name="HR"),
        role=Role(id="role_mgr", title="HR Manager"),
        status="normal",
        risk_score=78,
        last_login=LastLogin(timestamp="2025-10-24T14:50:00Z", relative="1 hour ago"),
        location=Location(city="London", country="UK", is_suspicious=False),
        device=Device(type="laptop", os="Windows 10", browser="Edge"),
        anomalies=Anoms(today=1, this_week=5),
    ),
]

def _filter_users(users: List[UserOut], status: str, department: str, q: str) -> List[UserOut]:
    out = users
    if status != "all":
        status_norm = status.replace("-", "_").lower()
        out = [u for u in out if u.status == status_norm]
    if department != "all":
        out = [u for u in out if u.department.name.lower() == department.lower()]
    if q:
        ql = q.lower()
        out = [u for u in out if ql in u.username.lower() or ql in u.full_name.lower() or ql in u.department.name.lower()]
    return out

@router.get("", response_model=UsersResp)
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: str = Query("all"),
    department: str = Query("all"),
    search: str = Query(""),
):
    filtered = _filter_users(_MOCK_USERS, status, department, search)
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    slice_ = filtered[start:end]
    total_pages = max(1, (total + per_page - 1) // per_page)
    return {
        "users": slice_,
        "pagination": {
            "page": page, "per_page": per_page, "total_pages": total_pages, "total_count": total
        },
        "filters_applied": {"status": status, "department": department, "search_query": search},
    }

@router.get("/statistics", response_model=UsersStatsResp)
def users_statistics():
    total = len(_MOCK_USERS)
    by = {"normal": 0, "investigating": 0, "high_risk": 0}
    for u in _MOCK_USERS:
        by[u.status] = by.get(u.status, 0) + 1
    return {"total_users": total, "by_status": by}
