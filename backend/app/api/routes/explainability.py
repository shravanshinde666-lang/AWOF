from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.explainability import ExplainabilityResult, LocalExplanation
from ...services.explainability_service import (
    ExplainabilityNotFoundError,
    ExplainabilityPrerequisiteError,
    InvalidExplanationRowError,
    generate_explainability,
    get_explainability,
    get_local_explanation,
)


router = APIRouter(prefix="/datasets", tags=["Explainability"])


def _response(action):
    try:
        return action()
    except ExplainabilityPrerequisiteError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except ExplainabilityNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})
    except InvalidExplanationRowError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})


@router.post("/{dataset_id}/explain", response_model=ExplainabilityResult)
async def generate(dataset_id: str):
    return _response(lambda: generate_explainability(dataset_id))


@router.get("/{dataset_id}/explainability", response_model=ExplainabilityResult)
async def retrieve(dataset_id: str):
    return _response(lambda: get_explainability(dataset_id))


@router.get("/{dataset_id}/explainability/{row_index}", response_model=LocalExplanation)
async def local(dataset_id: str, row_index: int):
    return _response(lambda: get_local_explanation(dataset_id, row_index))
