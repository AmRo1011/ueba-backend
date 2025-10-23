from fastapi import APIRouter, Depends, Query
from app.api.deps import get_uow, require_role
from app.core.responses import ok
from app.domain.services.detection_service import DetectionService

router = APIRouter(prefix="/detection", tags=["detection"], dependencies=[Depends(require_role("admin"))])

@router.post("/run")
def run_detection(uow = Depends(get_uow), enabled: list[str] | None = Query(None)):
    svc = DetectionService(uow)
    created = svc.run_all(enabled)
    return ok({"created": created})
