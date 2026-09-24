from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ...schemas.business import BusinessIntelligenceResult
from ...services.business_service import BusinessPrerequisiteError, BusinessResultNotFoundError, generate_business_priority, get_business_priority


router = APIRouter(prefix="/datasets", tags=["Business Priority / CIPS"])


def _limit(value: int) -> int:
    return max(1, min(value, 1000))


def _response(action):
    try:
        return action()
    except BusinessPrerequisiteError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except BusinessResultNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})


@router.post("/{dataset_id}/business-priority", response_model=BusinessIntelligenceResult)
async def generate(dataset_id: str, limit: int = Query(default=100, ge=1, le=1000)):
    return _response(lambda: generate_business_priority(dataset_id, _limit(limit)))


@router.get("/{dataset_id}/business-priority", response_model=BusinessIntelligenceResult)
async def retrieve(dataset_id: str, limit: int = Query(default=100, ge=1, le=1000)):
    return _response(lambda: get_business_priority(dataset_id, _limit(limit)))
