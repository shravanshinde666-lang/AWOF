from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from ...schemas.model import AMRAResult, ModelEvaluationResult, TrainingJobStatus
from ...services.model_service import (
    ModelPrerequisiteError,
    ModelResultNotFoundError,
    get_evaluation,
    get_recommendations,
    get_model_training_status,
    recommend_models,
    run_model_training_job,
    start_model_training,
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


@router.post("/{dataset_id}/models/train-job", response_model=TrainingJobStatus, status_code=202)
def start_training_job(dataset_id: str, background_tasks: BackgroundTasks):
    status = _response(lambda: start_model_training(dataset_id))
    if isinstance(status, JSONResponse):
        return status
    if status.pop("_schedule", False):
        background_tasks.add_task(run_model_training_job, dataset_id)
    return status


@router.get("/{dataset_id}/models/train-job", response_model=TrainingJobStatus)
def training_status(dataset_id: str):
    return _response(lambda: get_model_training_status(dataset_id))


@router.get("/{dataset_id}/models/evaluation", response_model=ModelEvaluationResult)
async def evaluation(dataset_id: str):
    return _response(lambda: get_evaluation(dataset_id))
