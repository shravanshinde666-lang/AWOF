"""Focused Phase 9 persistence coverage using an isolated SQLite database."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.database.connection import configure_database, init_database, session_scope
from backend.app.database.models import DatasetRecord
from backend.app.database import repository
from backend.app.main import app


def _metadata(dataset_id: str, stored_filename: str = "safe.csv") -> dict:
    return {
        "dataset_id": dataset_id,
        "original_filename": "safe.csv",
        "stored_filename": stored_filename,
        "file_type": "csv",
        "file_size_bytes": 10,
        "rows": 2,
        "columns": 2,
        "column_names": ["feature", "target"],
        "preview": [{"feature": 1, "target": "yes"}],
        "sheet_name": None,
    }


class PersistenceTests(TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.database_url = f"sqlite:///{Path(self.temporary.name, 'awof-test.db').as_posix()}"
        configure_database(self.database_url)
        init_database()

    def tearDown(self) -> None:
        configure_database()
        self.temporary.cleanup()

    def test_stage_state_survives_new_database_session(self) -> None:
        dataset_id = str(uuid4())
        repository.save_dataset(dataset_id, _metadata(dataset_id))
        repository.save_stage(dataset_id, "profile", {"dataset_id": dataset_id, "summary": {"rows": 2}})
        repository.save_stage(dataset_id, "configuration", {"valid": True, "problem_type": "classification"})

        # A fresh engine/session simulates service recreation after restart.
        configure_database(self.database_url)
        self.assertEqual(repository.get_dataset(dataset_id)["original_filename"], "safe.csv")
        self.assertTrue(repository.get_stage(dataset_id, "configuration")["valid"])

    def test_full_stage_history_and_experiment_history_persist(self) -> None:
        dataset_id = str(uuid4())
        repository.save_dataset(dataset_id, _metadata(dataset_id))
        for stage in (
            "profile", "configuration", "capabilities", "workflow", "pruned_workflow",
            "execution", "model_recommendations", "model_evaluation", "explainability", "business_priority",
        ):
            repository.save_stage(dataset_id, stage, {"stage": stage})
        experiment_id = str(uuid4())
        repository.save_experiment(experiment_id, dataset_id, {
            "experiment_id": experiment_id, "dataset_id": dataset_id, "dataset_name": "safe.csv",
            "problem_type": "classification", "objective": "predict_behavior", "timestamp": "2026-09-23T00:00:00+00:00",
            "metadata": {"runs": 1},
        })

        self.assertEqual(len(repository.get_history(dataset_id)), 10)
        self.assertEqual(repository.get_experiment(experiment_id)["dataset_id"], dataset_id)
        self.assertEqual(len(repository.list_experiments(dataset_id)), 1)

    def test_delete_removes_database_state(self) -> None:
        dataset_id = str(uuid4())
        repository.save_dataset(dataset_id, _metadata(dataset_id))
        repository.save_stage(dataset_id, "profile", {"ok": True})
        repository.delete_dataset(dataset_id)
        with self.assertRaises(repository.PersistenceNotFoundError):
            repository.get_dataset(dataset_id)
        with self.assertRaises(repository.PersistenceNotFoundError):
            repository.get_stage(dataset_id, "profile")

    def test_invalid_identifier_is_safe_and_transaction_rolls_back(self) -> None:
        with self.assertRaises(repository.PersistenceNotFoundError):
            repository.get_dataset("../../not-a-uuid")
        dataset_id = str(uuid4())
        repository.save_dataset(dataset_id, _metadata(dataset_id))
        with self.assertRaises(IntegrityError):
            with session_scope() as session:
                session.add(DatasetRecord(
                    id=str(uuid4()), original_filename="second.csv", stored_filename="safe.csv",
                    metadata_json=_metadata(str(uuid4()), "safe.csv"),
                ))
        self.assertEqual(repository.get_dataset(dataset_id)["stored_filename"], "safe.csv")

    def test_project_api_rejects_invalid_identifier_without_traceback(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/datasets/not-a-valid-uuid/history")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Dataset not found")

    def test_project_api_lists_history_and_deletes_safely(self) -> None:
        dataset_id = str(uuid4())
        repository.save_dataset(dataset_id, _metadata(dataset_id, "delete-safe.csv"))
        repository.save_stage(dataset_id, "profile", {"ok": True})
        client = TestClient(app)
        self.assertTrue(any(item["dataset_id"] == dataset_id for item in client.get("/api/v1/datasets").json()))
        self.assertEqual(client.get(f"/api/v1/datasets/{dataset_id}/history").status_code, 200)
        self.assertEqual(client.delete(f"/api/v1/datasets/{dataset_id}").status_code, 200)
        self.assertEqual(client.get(f"/api/v1/datasets/{dataset_id}").status_code, 404)

    def test_initial_alembic_migration_runs_on_a_fresh_sqlite_database(self) -> None:
        database_path = Path(self.temporary.name, "migration-test.db")
        environment = {**os.environ, "DATABASE_URL": f"sqlite:///{database_path.as_posix()}"}
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
