from fastapi import APIRouter
from fastapi.responses import JSONResponse

from awof.profiler.dataset_profiler import DatasetProfiler

from ...schemas.profile import DatasetProfile
from ...services.dataset_service import (
    DatasetNotFoundError,
    get_profile,
    load_dataset_dataframe,
    store_profile,
)
from ...services.insight_service import get_visual_insights


router = APIRouter(prefix="/datasets", tags=["Profiling / Dataset Intelligence"])


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": message},
    )


@router.post("/{dataset_id}/profile", response_model=DatasetProfile)
async def generate_dataset_profile(
    dataset_id: str,
) -> DatasetProfile | JSONResponse:
    try:
        dataframe = load_dataset_dataframe(dataset_id)
        profile = DatasetProfiler(dataframe).generate_profile()
        profile["dataset_id"] = dataset_id
        store_profile(dataset_id, profile)
        return DatasetProfile.model_validate(profile)
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
async def retrieve_dataset_profile(
    dataset_id: str,
) -> DatasetProfile | JSONResponse:
    try:
        return DatasetProfile.model_validate(get_profile(dataset_id))
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.get("/{dataset_id}/insights", response_model=None)
async def retrieve_visual_insights(dataset_id: str):
    try:
        return get_visual_insights(dataset_id)
    except DatasetNotFoundError as error:
        return error_response(404, str(error))
