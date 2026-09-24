from typing import Any

from pydantic import BaseModel


class DatasetSummary(BaseModel):
    rows: int
    columns: int
    total_cells: int
    missing_cells: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    memory_usage_bytes: int
    numerical_columns: int
    categorical_columns: int
    boolean_columns: int
    datetime_columns: int
    text_columns: int


class ColumnTypeInfo(BaseModel):
    column: str
    pandas_dtype: str
    detected_type: str
    broad_type: str
    nullable: bool
    unique_count: int
    unique_percentage: float
    cardinality: str
    is_constant: bool
    is_identifier_candidate: bool


class DatasetProfile(BaseModel):
    dataset_id: str
    summary: DatasetSummary
    column_types: list[ColumnTypeInfo]
    columns: dict[str, dict[str, Any]]
    quality: dict[str, Any]
    correlations: dict[str, Any]
    generated_at: str
