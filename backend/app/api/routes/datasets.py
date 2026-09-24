from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse

from ...schemas.dataset import DatasetMetadata, DatasetPreviewResponse, DatasetUploadResponse
from ...services.dataset_service import (
    DatasetNotFoundError,
    DatasetValidationError,
    delete_dataset,
    get_dataset,
    get_dataset_history,
    get_dataset_preview,
    get_dataset_summary,
    ingest_dataset,
    list_datasets,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": False, "error": message})


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetUploadResponse | JSONResponse:
    try:
        dataset = await ingest_dataset(file)
    except DatasetValidationError as error:
        return error_response(400, str(error))
    return DatasetUploadResponse(message="Dataset uploaded successfully", dataset=dataset)


@router.get("", response_model=list[DatasetMetadata])
async def list_dataset_projects() -> list[DatasetMetadata]:
    return list_datasets()


@router.get("/{dataset_id}", response_model=DatasetMetadata)
async def retrieve_dataset(dataset_id: str) -> DatasetMetadata | JSONResponse:
    try:
        return get_dataset(dataset_id)
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def retrieve_dataset_preview(dataset_id: str, limit: int = Query(10, ge=1, le=100)) -> DatasetPreviewResponse | JSONResponse:
    try:
        return DatasetPreviewResponse(dataset_id=dataset_id, rows=get_dataset_preview(dataset_id, limit))
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.get("/{dataset_id}/summary", response_model=None)
async def retrieve_dataset_summary(dataset_id: str) -> dict | JSONResponse:
    try:
        return get_dataset_summary(dataset_id)
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.get("/{dataset_id}/history", response_model=None)
async def retrieve_dataset_history(dataset_id: str) -> dict | JSONResponse:
    try:
        return {"dataset_id": dataset_id, "stages": get_dataset_history(dataset_id)}
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.delete("/{dataset_id}", response_model=None)
async def delete_dataset_project(dataset_id: str) -> dict | JSONResponse:
    try:
        delete_dataset(dataset_id)
        return {"success": True, "dataset_id": dataset_id, "message": "Dataset and persisted stage records were deleted."}
    except DatasetNotFoundError as error:
        return error_response(404, str(error))
