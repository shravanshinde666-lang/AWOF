from typing import Any

from pydantic import BaseModel


class DatasetMetadata(BaseModel):
    dataset_id: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size_bytes: int
    rows: int
    columns: int
    column_names: list[str]
    preview: list[dict[str, Any]]
    sheet_name: str | None = None


class DatasetUploadResponse(BaseModel):
    success: bool = True
    message: str
    dataset: DatasetMetadata


class DatasetPreviewResponse(BaseModel):
    success: bool = True
    dataset_id: str
    rows: list[dict[str, Any]]
