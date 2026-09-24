"""Final, compact API audit for the complete production-facing AWOF flow."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest import TestCase

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.config.settings import BACKEND_DIR
from backend.app.database.connection import configure_database
from backend.app.main import app


def _classification_frame() -> pd.DataFrame:
    values = list(range(30))
    return pd.DataFrame({
        "customer_id": [f"customer-{value:02d}" for value in values],
        "monthly_spend": [70 + (value % 6) * 11 for value in values],
        "plan": ["basic", "premium", "standard"] * 10,
        "churn": ["no"] * 15 + ["yes"] * 15,
    })


def _regression_frame() -> pd.DataFrame:
    values = list(range(30))
    return pd.DataFrame({
        "account_id": [f"account-{value:02d}" for value in values],
        "usage": [value % 8 + 1 for value in values],
        "tier": ["small", "medium", "large"] * 10,
        "revenue": [100.0 + value * 4.0 + (value % 3) for value in values],
    })


def _clustering_frame() -> pd.DataFrame:
    values = list(range(30))
    return pd.DataFrame({
        "entity_id": [f"entity-{value:02d}" for value in values],
        "spend": [20 + (value % 10) * 8 for value in values],
        "visits": [1 + value % 6 for value in values],
        "segment_hint": ["a"] * 10 + ["b"] * 10 + ["c"] * 10,
    })


class EndToEndAuditTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def _upload_csv(self, dataframe: pd.DataFrame, name: str) -> str:
        response = self.client.post(
            "/api/v1/datasets/upload",
            files={"file": (name, dataframe.to_csv(index=False).encode("utf-8"), "text/csv")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["dataset"]["dataset_id"]

    def _prepare(self, dataset_id: str, objective: str, target: str | None) -> None:
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/profile").status_code, 200)
        configuration = {"business_objective": objective, "target_column": target}
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/configuration", json=configuration).status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/capabilities").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/workflow").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/workflow/prune").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/execute").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/models/recommend").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/models/train").status_code, 200)

    def _delete(self, dataset_id: str) -> None:
        self.assertEqual(self.client.delete(f"/api/v1/datasets/{dataset_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}").status_code, 404)

    def test_complete_classification_research_persistence_and_deletion(self) -> None:
        dataset_id = self._upload_csv(_classification_frame(), "audit_classification.csv")
        self._prepare(dataset_id, "analyze_retention", "churn")
        evaluation = self.client.get(f"/api/v1/datasets/{dataset_id}/models/evaluation")
        self.assertEqual(evaluation.status_code, 200)
        artifact = evaluation.json()["best_model"]["artifact_filename"]
        self.assertEqual(Path(artifact).name, artifact)
        artifact_path = BACKEND_DIR.parent / "storage" / "models" / artifact
        self.assertTrue(artifact_path.is_file())
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/explain").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/business-priority").status_code, 200)
        experiment = self.client.post(f"/api/v1/datasets/{dataset_id}/experiments/compare", json={"runs": 1})
        self.assertEqual(experiment.status_code, 200, experiment.text)
        experiment_id = experiment.json()["experiment_id"]
        self.assertEqual(self.client.get(f"/api/v1/experiments/{experiment_id}").status_code, 200)

        # Replacing the SQLAlchemy engine simulates a new service/session after restart.
        configure_database()
        history = self.client.get(f"/api/v1/datasets/{dataset_id}/history")
        self.assertEqual(history.status_code, 200)
        self.assertIn("model_evaluation", {item["stage"] for item in history.json()["stages"]})
        self._delete(dataset_id)
        self.assertFalse(artifact_path.exists())

    def test_regression_and_clustering_stage_flows(self) -> None:
        regression_id = self._upload_csv(_regression_frame(), "audit_regression.csv")
        self._prepare(regression_id, "optimize_revenue", "revenue")
        self.assertEqual(self.client.post(f"/api/v1/datasets/{regression_id}/explain").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{regression_id}/business-priority").status_code, 200)
        self._delete(regression_id)

        clustering_id = self._upload_csv(_clustering_frame(), "audit_clustering.csv")
        self._prepare(clustering_id, "segment_customers", None)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{clustering_id}/explain").status_code, 200)
        business = self.client.post(f"/api/v1/datasets/{clustering_id}/business-priority")
        self.assertEqual(business.status_code, 200)
        self.assertEqual(business.json()["applicability"], "not_applicable")
        self._delete(clustering_id)

    def test_xlsx_upload_and_profile(self) -> None:
        buffer = BytesIO()
        _classification_frame().to_excel(buffer, index=False)
        response = self.client.post(
            "/api/v1/datasets/upload",
            files={"file": ("audit.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        dataset_id = response.json()["dataset"]["dataset_id"]
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/profile").status_code, 200)
        self._delete(dataset_id)
