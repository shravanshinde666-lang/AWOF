import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from joblib import load
from sklearn.pipeline import Pipeline

from backend.app.config.settings import BACKEND_DIR
from backend.app.main import app


class DatasetUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        response = self.client.post(
            "/api/v1/datasets/upload",
            files={
                "file": (
                    "customers.csv",
                    b"customer_id,age\nC001,23\nC002,35\nC003,41\n",
                    "text/csv",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.dataset_id = response.json()["dataset"]["dataset_id"]

    def test_valid_csv_upload(self) -> None:
        response = self.client.get(f"/api/v1/datasets/{self.dataset_id}")
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["rows"], 3)
        self.assertEqual(body["columns"], 2)

    def test_unsupported_extension_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/datasets/upload",
            files={"file": ("unsafe.pdf", b"not a dataset", "application/pdf")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_empty_dataset_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/datasets/upload",
            files={"file": ("empty.csv", b"customer_id,age\n", "text/csv")},
        )
        self.assertEqual(response.status_code, 400)

    def test_metadata_lookup(self) -> None:
        response = self.client.get(f"/api/v1/datasets/{self.dataset_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dataset_id"], self.dataset_id)

    def test_unknown_dataset_returns_404(self) -> None:
        response = self.client.get("/api/v1/datasets/unknown-dataset")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_preview_limit(self) -> None:
        response = self.client.get(
            f"/api/v1/datasets/{self.dataset_id}/preview?limit=2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["rows"]), 2)

    def test_generate_and_retrieve_profile(self) -> None:
        generated = self.client.post(
            f"/api/v1/datasets/{self.dataset_id}/profile"
        )
        self.assertEqual(generated.status_code, 200)
        self.assertEqual(generated.json()["summary"]["rows"], 3)

        retrieved = self.client.get(
            f"/api/v1/datasets/{self.dataset_id}/profile"
        )
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.json()["dataset_id"], self.dataset_id)

    def test_configuration_flow(self) -> None:
        profile = self.client.post(f"/api/v1/datasets/{self.dataset_id}/profile")
        self.assertEqual(profile.status_code, 200)
        candidates = self.client.get(f"/api/v1/datasets/{self.dataset_id}/target-candidates")
        self.assertEqual(candidates.status_code, 200)
        self.assertTrue(candidates.json()["candidates"])
        saved = self.client.post(
            f"/api/v1/datasets/{self.dataset_id}/configuration",
            json={"business_objective": "segment_customers", "target_column": None},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["configuration"]["problem_type"], "clustering")
        retrieved = self.client.get(f"/api/v1/datasets/{self.dataset_id}/configuration")
        self.assertEqual(retrieved.status_code, 200)

    def test_capability_flow(self) -> None:
        self.assertEqual(self.client.post(f"/api/v1/datasets/{self.dataset_id}/profile").status_code, 200)
        self.assertEqual(self.client.post(
            f"/api/v1/datasets/{self.dataset_id}/configuration",
            json={"business_objective": "segment_customers", "target_column": None},
        ).status_code, 200)
        generated = self.client.post(f"/api/v1/datasets/{self.dataset_id}/capabilities")
        self.assertEqual(generated.status_code, 200)
        self.assertEqual(len(generated.json()["capabilities"]), 15)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{self.dataset_id}/capabilities").status_code, 200)

    def test_workflow_flow(self) -> None:
        self.client.post(f"/api/v1/datasets/{self.dataset_id}/profile")
        self.client.post(f"/api/v1/datasets/{self.dataset_id}/configuration", json={"business_objective": "segment_customers", "target_column": None})
        self.client.post(f"/api/v1/datasets/{self.dataset_id}/capabilities")
        response = self.client.post(f"/api/v1/datasets/{self.dataset_id}/workflow")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["validation"]["is_dag"])

    def test_full_prune_and_execute_flow(self) -> None:
        self.assertEqual(self.client.post(f"/api/v1/datasets/{self.dataset_id}/profile").status_code, 200)
        self.assertEqual(
            self.client.post(
                f"/api/v1/datasets/{self.dataset_id}/configuration",
                json={"business_objective": "segment_customers", "target_column": None},
            ).status_code,
            200,
        )
        self.assertEqual(self.client.post(f"/api/v1/datasets/{self.dataset_id}/capabilities").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{self.dataset_id}/workflow").status_code, 200)

        pruned = self.client.post(f"/api/v1/datasets/{self.dataset_id}/workflow/prune")
        self.assertEqual(pruned.status_code, 200)
        evidence = pruned.json()["pruned_nodes"]
        self.assertTrue(evidence)
        self.assertTrue(all(node["reason"] for node in evidence))

        executed = self.client.post(f"/api/v1/datasets/{self.dataset_id}/execute")
        self.assertEqual(executed.status_code, 200)
        self.assertIn("summary", executed.json())
        self.assertEqual(
            self.client.get(f"/api/v1/datasets/{self.dataset_id}/workflow/pruned").json()["pruned_nodes"],
            evidence,
        )

    def test_full_model_recommendation_training_and_evaluation_flow(self) -> None:
        rows = ["record_id,age,spend,churn"]
        rows.extend(f"r{index},{20 + index % 18},{100 + index * 7},{'no' if index < 20 else 'yes'}" for index in range(40))
        upload = self.client.post(
            "/api/v1/datasets/upload",
            files={"file": ("classification.csv", ("\n".join(rows) + "\n").encode(), "text/csv")},
        )
        self.assertEqual(upload.status_code, 200)
        dataset_id = upload.json()["dataset"]["dataset_id"]
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/profile").status_code, 200)
        self.assertEqual(self.client.post(
            f"/api/v1/datasets/{dataset_id}/configuration",
            json={"business_objective": "analyze_retention", "target_column": "churn"},
        ).status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/capabilities").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/workflow").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/workflow/prune").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/execute").status_code, 200)

        recommendations = self.client.post(f"/api/v1/datasets/{dataset_id}/models/recommend")
        self.assertEqual(recommendations.status_code, 200)
        self.assertTrue(recommendations.json()["summary"]["models_recommended"])
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}/models/recommendations").status_code, 200)

        training = self.client.post(f"/api/v1/datasets/{dataset_id}/models/train")
        self.assertEqual(training.status_code, 200)
        body = training.json()
        self.assertTrue(any(result["status"] == "completed" for result in body["results"]))
        self.assertIsNotNone(body["best_model"])
        artifact_filename = body["best_model"]["artifact_filename"]
        self.assertTrue(artifact_filename.endswith(".joblib"))
        artifact_path = Path(BACKEND_DIR).parent / "storage" / "models" / artifact_filename
        self.assertTrue(artifact_path.is_file())
        self.assertIsInstance(load(artifact_path), Pipeline)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}/models/evaluation").status_code, 200)

        explained = self.client.post(f"/api/v1/datasets/{dataset_id}/explain")
        self.assertEqual(explained.status_code, 200)
        self.assertTrue(explained.json()["global_importance"])
        self.assertTrue(explained.json()["local_explanations"])
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}/explainability").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}/explainability/0").status_code, 200)

        priorities = self.client.post(f"/api/v1/datasets/{dataset_id}/business-priority")
        self.assertEqual(priorities.status_code, 200)
        priority_body = priorities.json()
        self.assertTrue(priority_body["items"])
        self.assertEqual(priority_body["items"], sorted(priority_body["items"], key=lambda item: (-item["cips_score"], item["row_index"])))
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}/business-priority").status_code, 200)


if __name__ == "__main__":
    unittest.main()
