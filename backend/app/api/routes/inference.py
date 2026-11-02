from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.inference import (
    InferenceSchemaResponse,
    PredictionRequest,
    PredictionResponse,
)
from ...services.inference_service import (
    InferenceError,
    get_inference_schema,
    run_live_inference,
)

router = APIRouter(prefix="/datasets", tags=["Live Inference & Counterfactual Playground"])


@router.get("/{dataset_id}/inference/schema", response_model=InferenceSchemaResponse)
async def get_schema(dataset_id: str):
    try:
        return get_inference_schema(dataset_id)
    except InferenceError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})


@router.post("/{dataset_id}/inference/predict", response_model=PredictionResponse)
async def predict_live(dataset_id: str, request: PredictionRequest):
    try:
        return run_live_inference(
            dataset_id=dataset_id,
            features=request.features,
            target_class=request.target_class,
        )
    except InferenceError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
