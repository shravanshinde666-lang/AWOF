from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.model import AMRAResult, ModelEvaluationResult
from ...services.model_service import (
    ModelPrerequisiteError,
    ModelResultNotFoundError,
    get_evaluation,
    get_recommendations,
    recommend_models,
    train_models,
)


router = APIRouter(prefix="/datasets", tags=["AMRA and Machine Learning"])


def _response(action):
    try:
        return action()
    except ModelPrerequisiteError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except ModelResultNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})


@router.post("/{dataset_id}/models/recommend", response_model=AMRAResult)
async def recommend(dataset_id: str):
    return _response(lambda: recommend_models(dataset_id))


@router.get("/{dataset_id}/models/recommendations", response_model=AMRAResult)
async def recommendations(dataset_id: str):
    return _response(lambda: get_recommendations(dataset_id))


@router.post("/{dataset_id}/models/train", response_model=ModelEvaluationResult)
async def train(dataset_id: str):
    return _response(lambda: train_models(dataset_id))


@router.get("/{dataset_id}/models/evaluation", response_model=ModelEvaluationResult)
async def evaluation(dataset_id: str):
    return _response(lambda: get_evaluation(dataset_id))
