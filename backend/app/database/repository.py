"""JSON-oriented repository preserving AWOF's existing algorithm result shapes."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select

from .connection import session_scope
from .models import DatasetRecord, ExperimentRecord, StageRecord


class PersistenceNotFoundError(Exception):
    pass


class PersistenceConflictError(Exception):
    pass


def _uuid(value: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise PersistenceNotFoundError("Resource not found.") from exc


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def save_dataset(dataset_id: str, metadata: dict[str, Any]) -> None:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        if session.get(DatasetRecord, dataset_id) is not None:
            raise PersistenceConflictError("Dataset already exists.")
        session.add(DatasetRecord(id=dataset_id, original_filename=str(metadata["original_filename"]), stored_filename=str(metadata["stored_filename"]), metadata_json=_json_safe(metadata)))


def get_dataset(dataset_id: str) -> dict[str, Any]:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        record = session.get(DatasetRecord, dataset_id)
        if record is None:
            raise PersistenceNotFoundError("Dataset not found")
        return deepcopy(record.metadata_json)


def list_datasets() -> list[dict[str, Any]]:
    with session_scope() as session:
        records = session.scalars(select(DatasetRecord).order_by(DatasetRecord.created_at.desc())).all()
        return [deepcopy(record.metadata_json) for record in records]


def get_stored_filename(dataset_id: str) -> str:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        record = session.get(DatasetRecord, dataset_id)
        if record is None:
            raise PersistenceNotFoundError("Dataset not found")
        return record.stored_filename


def save_stage(dataset_id: str, stage: str, payload: dict[str, Any]) -> None:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        if session.get(DatasetRecord, dataset_id) is None:
            raise PersistenceNotFoundError("Dataset not found")
        record = session.scalar(select(StageRecord).where(StageRecord.dataset_id == dataset_id, StageRecord.stage == stage))
        if record is None:
            session.add(StageRecord(dataset_id=dataset_id, stage=stage, payload=_json_safe(payload)))
        else:
            record.payload = _json_safe(payload)


def get_stage(dataset_id: str, stage: str) -> dict[str, Any]:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        if session.get(DatasetRecord, dataset_id) is None:
            raise PersistenceNotFoundError("Dataset not found")
        record = session.scalar(select(StageRecord).where(StageRecord.dataset_id == dataset_id, StageRecord.stage == stage))
        if record is None:
            raise PersistenceNotFoundError(f"{stage} has not been generated.")
        return deepcopy(record.payload)


def get_history(dataset_id: str) -> list[dict[str, Any]]:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        if session.get(DatasetRecord, dataset_id) is None:
            raise PersistenceNotFoundError("Dataset not found")
        records = session.scalars(select(StageRecord).where(StageRecord.dataset_id == dataset_id).order_by(StageRecord.updated_at)).all()
        return [{"stage": record.stage, "updated_at": record.updated_at.isoformat()} for record in records]


def save_experiment(experiment_id: str, dataset_id: str, payload: dict[str, Any]) -> None:
    experiment_id, dataset_id = _uuid(experiment_id), _uuid(dataset_id)
    with session_scope() as session:
        if session.get(DatasetRecord, dataset_id) is None:
            raise PersistenceNotFoundError("Dataset not found")
        existing = session.get(ExperimentRecord, experiment_id)
        if existing is None:
            session.add(ExperimentRecord(id=experiment_id, dataset_id=dataset_id, payload=_json_safe(payload)))
        else:
            existing.payload = _json_safe(payload)


def get_experiment(experiment_id: str) -> dict[str, Any]:
    experiment_id = _uuid(experiment_id)
    with session_scope() as session:
        record = session.get(ExperimentRecord, experiment_id)
        if record is None:
            raise PersistenceNotFoundError("Experiment not found.")
        return deepcopy(record.payload)


def list_experiments(dataset_id: str) -> list[dict[str, Any]]:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        records = session.scalars(select(ExperimentRecord).where(ExperimentRecord.dataset_id == dataset_id).order_by(ExperimentRecord.created_at.desc())).all()
        return [deepcopy(record.payload) for record in records]


def delete_dataset(dataset_id: str) -> dict[str, Any]:
    dataset_id = _uuid(dataset_id)
    with session_scope() as session:
        record = session.get(DatasetRecord, dataset_id)
        if record is None:
            raise PersistenceNotFoundError("Dataset not found")
        result = {"stored_filename": record.stored_filename}
        session.execute(delete(StageRecord).where(StageRecord.dataset_id == dataset_id))
        session.execute(delete(ExperimentRecord).where(ExperimentRecord.dataset_id == dataset_id))
        session.delete(record)
        return result
