from fastapi import APIRouter, UploadFile, Depends, HTTPException
from app.api.deps import get_uow, require_role
from app.core.responses import ok
from app.domain.entities.log import LogEntity
from app.domain.entities.user import UserEntity

import io, csv, json
from datetime import datetime, timezone

# ?????? ??????: admin/analyst
router = APIRouter(prefix="/data", tags=["data"], dependencies=[Depends(require_role("admin","analyst"))])

def _parse_ts(val: str) -> datetime:
    s = str(val).strip().replace(" ", "T")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        raise ValueError(f"Invalid ISO timestamp: {val}")

def _read_rows(raw: bytes):
    text = raw.decode(errors="ignore").lstrip()
    if text.startswith("{") or text.startswith("["):
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("rows") or data.get("data") or []
        if not isinstance(data, list):
            raise ValueError("JSON must be a list of objects")
        for obj in data:
            yield { (k.lower() if isinstance(k,str) else k): v for k,v in obj.items() }
    else:
        f = io.StringIO(text)
        reader = csv.DictReader(f)
        for row in reader:
            yield { (k.lower() if isinstance(k,str) else k): v for k,v in row.items() }

@router.post("/upload-logs")
async def upload_logs(file: UploadFile, uow = Depends(get_uow)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    required = {"uid","timestamp","activity_type"}
    inserted = 0
    buffer: list[LogEntity] = []

    try:
        for r in _read_rows(raw):
            if not required.issubset(r.keys()):
                missing = required - set(r.keys())
                raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

            uid = str(r.get("uid")).strip()
            u = uow.users.get_by_uid(uid)
            if not u:
                u = uow.users.add(UserEntity(
                    id=None, uid=uid,
                    username=r.get("username"), email=r.get("email")
                ))

            ts = _parse_ts(r.get("timestamp"))
            hour = ts.hour

            at_code = str(r.get("activity_type")).strip()
            at_id = uow.logs.resolve_activity_type_id(at_code)

            buffer.append(LogEntity(
                id=None, user_id=u.id, ts=ts, activity_type_id=at_id,
                source_ip=r.get("source_ip"),
                params=r, hour=hour,
                is_weekend=None, is_night=None
            ))

            if len(buffer) >= 5000:
                inserted += uow.logs.bulk_add(buffer)
                buffer.clear()

        if buffer:
            inserted += uow.logs.bulk_add(buffer)

        uow.commit()
        return ok({"inserted": inserted})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"parse_error: {str(e)[:200]}")
