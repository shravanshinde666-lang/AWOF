import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile
from pandas.errors import EmptyDataError, ParserError

from ..config.settings import BACKEND_DIR, settings
from ..database import repository
from ..schemas.dataset import DatasetMetadata

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
CHUNK_SIZE = 1024 * 1024
logger = logging.getLogger(__name__)


class DatasetValidationError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


def _upload_directory() -> Path:
    directory = BACKEND_DIR.parent / settings.UPLOAD_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_filename(filename: str) -> str:
    basename = Path(filename.replace("\\", "/")).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", basename).strip("._")
    return safe_name or "dataset"


def validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise DatasetValidationError("Unsupported file type. Only CSV and Excel files are allowed.")
    return extension


async def save_upload(file: UploadFile) -> tuple[str, str, int, Path]:
    original_filename = file.filename or ""
    validate_extension(original_filename)
    dataset_id = str(uuid4())
    stored_filename = f"{dataset_id}_{sanitize_filename(original_filename)}"
    destination = _upload_directory() / stored_filename
    maximum = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size = 0
    try:
        with destination.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > maximum:
                    raise DatasetValidationError(f"File exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    if size == 0:
        destination.unlink(missing_ok=True)
        raise DatasetValidationError("The uploaded file is empty.")
    return dataset_id, stored_filename, size, destination


def load_dataframe(path: Path, extension: str) -> tuple[pd.DataFrame, str | None]:
    try:
        if extension == ".csv":
            for encoding in ("utf-8", "utf-8-sig", "latin-1"):
                try:
                    return pd.read_csv(path, encoding=encoding), None
                except UnicodeDecodeError:
                    continue
            raise DatasetValidationError("The CSV file could not be parsed.")
        # ExcelFile keeps an open handle on Windows.  Close it before callers
        # can safely delete the uploaded project artifact.
        with pd.ExcelFile(path, engine="openpyxl" if extension == ".xlsx" else "xlrd") as workbook:
            sheet_name = str(workbook.sheet_names[0])
            dataframe = pd.read_excel(workbook, sheet_name=0)
        return dataframe, sheet_name
    except DatasetValidationError:
        raise
    except (EmptyDataError, ParserError, UnicodeDecodeError, ValueError, OSError) as error:
        label = "CSV" if extension == ".csv" else "Excel"
        raise DatasetValidationError(f"The {label} file could not be parsed.") from error


def _preview(dataframe: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    return json.loads(dataframe.head(limit).to_json(orient="records", date_format="iso"))


async def ingest_dataset(file: UploadFile) -> DatasetMetadata:
    original_filename = file.filename or ""
    extension = validate_extension(original_filename)
    dataset_id, stored_filename, size, path = await save_upload(file)
    try:
        dataframe, sheet_name = load_dataframe(path, extension)
        if dataframe.empty or dataframe.shape[1] == 0:
            raise DatasetValidationError("The uploaded dataset is empty.")
        metadata = DatasetMetadata(
            dataset_id=dataset_id, original_filename=sanitize_filename(original_filename),
            stored_filename=stored_filename, file_type=extension.lstrip("."),
            file_size_bytes=size, rows=int(dataframe.shape[0]), columns=int(dataframe.shape[1]),
            column_names=[str(column) for column in dataframe.columns],
            preview=_preview(dataframe, 10), sheet_name=sheet_name,
        )
    except Exception:
        path.unlink(missing_ok=True)
        raise
    try:
        repository.save_dataset(dataset_id, metadata.model_dump())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return metadata


def _metadata(dataset_id: str) -> DatasetMetadata:
    try:
        return DatasetMetadata.model_validate(repository.get_dataset(dataset_id))
    except repository.PersistenceNotFoundError as exc:
        raise DatasetNotFoundError("Dataset not found") from exc


def get_dataset(dataset_id: str) -> DatasetMetadata:
    return _metadata(dataset_id)


def _dataset_path(metadata: DatasetMetadata) -> Path:
    safe_name = Path(metadata.stored_filename).name
    if safe_name != metadata.stored_filename:
        raise DatasetNotFoundError("Dataset artifact is unavailable")
    return _upload_directory() / safe_name


def get_dataset_preview(dataset_id: str, limit: int) -> list[dict[str, Any]]:
    metadata = _metadata(dataset_id)
    dataframe, _ = load_dataframe(_dataset_path(metadata), f".{metadata.file_type}")
    return _preview(dataframe, limit)


def load_dataset_dataframe(dataset_id: str) -> pd.DataFrame:
    metadata = _metadata(dataset_id)
    path = _dataset_path(metadata)
    if not path.is_file():
        raise DatasetNotFoundError("Dataset artifact is unavailable")
    dataframe, _ = load_dataframe(path, f".{metadata.file_type}")
    return dataframe


def store_profile(dataset_id: str, profile: dict[str, Any]) -> None:
    try:
        repository.save_stage(dataset_id, "profile", profile)
    except repository.PersistenceNotFoundError as exc:
        raise DatasetNotFoundError("Dataset not found") from exc


def get_profile(dataset_id: str) -> dict[str, Any]:
    try:
        return repository.get_stage(dataset_id, "profile")
    except repository.PersistenceNotFoundError as exc:
        message = str(exc)
        if message == "Dataset not found":
            raise DatasetNotFoundError(message) from exc
        raise DatasetNotFoundError("Dataset profile has not been generated") from exc


def list_datasets() -> list[DatasetMetadata]:
    return [DatasetMetadata.model_validate(item) for item in repository.list_datasets()]


def get_dataset_history(dataset_id: str) -> list[dict[str, Any]]:
    try:
        return repository.get_history(dataset_id)
    except repository.PersistenceNotFoundError as exc:
        raise DatasetNotFoundError("Dataset not found") from exc


def get_dataset_summary(dataset_id: str) -> dict[str, Any]:
    metadata = _metadata(dataset_id)
    return {"dataset": metadata.model_dump(), "stages": get_dataset_history(dataset_id)}


def delete_dataset(dataset_id: str) -> None:
    metadata = _metadata(dataset_id)
    try:
        experiments = repository.list_experiments(dataset_id)
        repository.delete_dataset(dataset_id)
    except repository.PersistenceNotFoundError as exc:
        raise DatasetNotFoundError("Dataset not found") from exc
    _dataset_path(metadata).unlink(missing_ok=True)
    model_dir = BACKEND_DIR.parent / "storage" / "models"
    if model_dir.is_dir():
        for artifact in model_dir.glob(f"{metadata.dataset_id}_*.joblib"):
            if artifact.parent == model_dir:
                try:
                    artifact.unlink()
                except OSError:
                    logger.warning("Could not remove model artifact for deleted dataset %s", metadata.dataset_id)
    results_root = BACKEND_DIR.parent / "experiments" / "results"
    for experiment in experiments:
        experiment_id = str(experiment.get("experiment_id") or "")
        # Database IDs are UUID-validated; this repeats a strict basename check
        # before removing per-experiment filesystem artifacts.
        if Path(experiment_id).name != experiment_id or len(experiment_id) != 36:
            continue
        (results_root / "metrics" / f"{experiment_id}.json").unlink(missing_ok=True)
        (results_root / "reports" / f"{experiment_id}.md").unlink(missing_ok=True)
        chart_directory = results_root / "charts" / experiment_id
        if chart_directory.is_dir() and chart_directory.parent == results_root / "charts":
            shutil.rmtree(chart_directory, ignore_errors=True)
