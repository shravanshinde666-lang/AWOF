"""Focused Phase 8 research-experiment tests.

The real runner tests deliberately use small synthetic frames.  Expensive
repeated-run aggregation and artifact writing are covered with deterministic
runner doubles so normal pytest does not become a benchmark suite itself.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from awof.amra.model_registry import models_for
from awof.profiler import DatasetProfiler
from backend.app.main import app
from backend.app.services import experiment_service
from experiments.adaptive.awof_pipeline import run_awof_pipeline
from experiments.baseline.fixed_pipeline import run_fixed_pipeline


def _classification_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [f"customer-{index:02d}" for index in range(30)],
            "age": [22 + index % 15 for index in range(30)],
            "monthly_spend": [80 + (index % 7) * 15 for index in range(30)],
            "plan": ["basic", "premium", "standard"] * 10,
            "churn": ["no"] * 15 + ["yes"] * 15,
        }
    )


def _regression_dataframe() -> pd.DataFrame:
    values = list(range(30))
    return pd.DataFrame(
        {
            "account_id": [f"account-{index:02d}" for index in values],
            "usage": [index % 9 + 1 for index in values],
            "tier": ["small", "medium", "large"] * 10,
            "revenue": [100.0 + index * 3.5 + (index % 4) * 2.0 for index in values],
        }
    )


def _configuration(problem_type: str, target: str | None) -> dict[str, object]:
    objective = "segment_customers" if problem_type == "clustering" else "predict_behavior"
    return {
        "dataset_id": "phase-8-test",
        "business_objective": {"id": objective, "label": objective.replace("_", " ").title()},
        "target": {"column": target} if target else None,
        "problem_type": problem_type,
        "valid": True,
    }


def _runner_fixture(name: str, *, modules: int, models: int, f1: float) -> dict[str, object]:
    """A minimal, JSON-safe runner result for aggregation/persistence tests."""

    return {
        "pipeline": name,
        "problem_type": "classification",
        "workflow_modules": {
            "considered": modules,
            "executed": modules,
            "selected": modules,
            "pruned": 0,
            "ids": ["classification"],
            "pruned_ids": [],
        },
        "models": {
            "considered": models,
            "selected": models,
            "trained": models,
            "failed": 0,
            "considered_ids": ["logistic_regression"],
            "selected_ids": ["logistic_regression"],
            "trained_ids": ["logistic_regression"],
            "failed_ids": [],
            "unavailable_ids": [],
            "best_model": {"model_id": "logistic_regression"},
            "best_metrics": {"f1": f1},
            "model_results": [],
        },
        "timings_ms": {"overall": 10.0 if name == "fixed_baseline" else 8.0, "model_training": 5.0},
        "resources": {"peak_python_memory_mb": 2.0 if name == "fixed_baseline" else 1.5, "cpu_process_time_ms": 3.0},
        "best_model": {"model_id": "logistic_regression"},
        "best_metrics": {"f1": f1},
        "split": {
            "strategy": "train_test_split",
            "random_state": 42,
            "test_size": 0.2,
            "train_rows": 24,
            "test_rows": 6,
            "test_index_fingerprint": "test-split",
        },
        "reproducibility": {"random_state": 42},
        "warnings": [],
    }


class ExperimentRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.classification_data = _classification_dataframe()
        cls.classification_configuration = _configuration("classification", "churn")
        cls.classification_profile = DatasetProfiler(
            cls.classification_data, "phase-8-test"
        ).generate_profile()
        cls.baseline = run_fixed_pipeline(
            cls.classification_data,
            cls.classification_configuration,
            cls.classification_profile,
            random_state=42,
            experiment_name="pytest-classification",
        )
        cls.awof = run_awof_pipeline(
            cls.classification_data,
            cls.classification_configuration,
            cls.classification_profile,
            random_state=42,
            experiment_name="pytest-classification",
        )

    def test_fixed_baseline_trains_every_available_classification_model(self) -> None:
        expected = {
            model["id"]
            for model in models_for("classification")
            if model["available"]
        }
        self.assertEqual(set(self.baseline["models"]["selected_ids"]), expected)
        self.assertEqual(set(self.baseline["models"]["trained_ids"]), expected)
        self.assertNotIn("xgboost_classifier", self.baseline["models"]["trained_ids"])

    def test_awof_uses_real_decision_stages_and_avoids_clean_unneeded_modules(self) -> None:
        for key in ("acsa", "awga", "pruning", "execution", "amra", "business_output"):
            self.assertIn(key, self.awof)
        self.assertTrue(self.awof["acsa"]["capabilities"])
        self.assertTrue(self.awof["awga"]["validation"]["is_dag"])
        self.assertIn("models", self.awof["amra"])
        self.assertLess(
            self.awof["workflow_modules"]["executed"],
            self.baseline["workflow_modules"]["executed"],
        )
        self.assertFalse(self.classification_data.isna().any().any())
        self.assertFalse(any(item["id"] == "text_preparation" for item in self.awof["awga"]["nodes"]))

    def test_supervised_pipelines_share_the_same_split_and_measurements(self) -> None:
        self.assertEqual(self.baseline["split"], self.awof["split"])
        for result in (self.baseline, self.awof):
            self.assertGreaterEqual(result["timings_ms"]["overall"], 0.0)
            self.assertGreaterEqual(result["resources"]["peak_python_memory_mb"], 0.0)
            self.assertIn("cpu_process_time_ms", result["resources"])
            self.assertIn("f1", result["best_metrics"])

    def test_amra_model_selection_reduces_real_regression_training(self) -> None:
        dataframe = _regression_dataframe()
        configuration = _configuration("regression", "revenue")
        profile = DatasetProfiler(dataframe, "phase-8-test").generate_profile()
        baseline = run_fixed_pipeline(dataframe, configuration, profile, random_state=42)
        adaptive = run_awof_pipeline(dataframe, configuration, profile, random_state=42)

        self.assertEqual(
            set(baseline["models"]["selected_ids"]),
            {
                model["id"]
                for model in models_for("regression")
                if model["available"]
            },
        )
        self.assertLess(adaptive["models"]["trained"], baseline["models"]["trained"])
        self.assertLess(adaptive["models"]["selected"], baseline["models"]["selected"])


class ExperimentServiceTests(unittest.TestCase):
    def test_repeated_runs_persist_json_csv_report_and_charts(self) -> None:
        dataframe = _classification_dataframe()
        configuration = _configuration("classification", "churn")
        profile = DatasetProfiler(dataframe, "phase-8-test").generate_profile()
        fixed = _runner_fixture("fixed_baseline", modules=5, models=3, f1=0.70)
        adaptive = _runner_fixture("awof_adaptive", modules=2, models=1, f1=0.69)

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            metrics_dir = root / "metrics"
            charts_dir = root / "charts"
            reports_dir = root / "reports"
            with (
                patch.object(experiment_service, "METRICS_DIR", metrics_dir),
                patch.object(experiment_service, "CHARTS_DIR", charts_dir),
                patch.object(experiment_service, "REPORTS_DIR", reports_dir),
                patch.object(experiment_service, "SUMMARY_PATH", root / "summary.csv"),
                patch.object(experiment_service.repository, "save_experiment"),
                patch.object(
                    experiment_service,
                    "get_dataset",
                    return_value=SimpleNamespace(original_filename="synthetic.csv"),
                ),
                patch.object(experiment_service, "get_profile", return_value=profile),
                patch.object(
                    experiment_service,
                    "get_saved_configuration",
                    return_value=configuration,
                ),
                patch.object(
                    experiment_service,
                    "load_dataset_dataframe",
                    return_value=dataframe,
                ),
                patch.object(
                    experiment_service,
                    "run_fixed_pipeline",
                    side_effect=[fixed, fixed],
                ) as baseline_runner,
                patch.object(
                    experiment_service,
                    "run_awof_pipeline",
                    side_effect=[adaptive, adaptive],
                ) as adaptive_runner,
            ):
                result = experiment_service.run_comparison(
                    "phase-8-test", runs=2, experiment_name="pytest-artifacts"
                )
                self.assertEqual(baseline_runner.call_count, 2)
                self.assertEqual(adaptive_runner.call_count, 2)
                self.assertEqual(
                    result["baseline"]["run_statistics"]["timings_ms"]["overall"],
                    {"mean": 10.0, "std": 0.0},
                )
                self.assertEqual(
                    result["awof"]["run_statistics"]["resources"]["peak_python_memory_mb"],
                    {"mean": 1.5, "std": 0.0},
                )
                self.assertEqual(result["comparison"]["module_reduction_count"], 3.0)
                self.assertEqual(result["comparison"]["model_reduction_count"], 2.0)
                self.assertEqual(
                    [item["run_index"] for item in result["run_results"]["baseline"]],
                    [1, 2],
                )

                experiment_id = result["experiment_id"]
                self.assertTrue((metrics_dir / f"{experiment_id}.json").is_file())
                self.assertTrue((root / "summary.csv").is_file())
                report = reports_dir / f"{experiment_id}.md"
                self.assertTrue(report.is_file())
                report_text = report.read_text(encoding="utf-8")
                for section in (
                    "## Dataset",
                    "## Experimental Setup",
                    "## Baseline Workflow",
                    "## AWOF Workflow",
                    "## Metrics",
                    "## Comparison",
                    "## Limitations",
                ):
                    self.assertIn(section, report_text)
                chart_dir = charts_dir / experiment_id
                self.assertEqual(
                    {path.name for path in chart_dir.glob("*.png")},
                    {
                        "execution_time.png",
                        "memory_usage.png",
                        "module_count.png",
                        "model_count.png",
                        "performance_comparison.png",
                    },
                )


class ExperimentApiIntegrationTests(unittest.TestCase):
    def test_compare_requires_a_profile_and_saved_configuration(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/v1/datasets/not-configured/experiments/compare",
            json={"runs": 1},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("required", response.json()["error"])

    def test_compare_validates_the_bounded_run_count(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/v1/datasets/not-configured/experiments/compare",
            json={"runs": 11},
        )
        self.assertEqual(response.status_code, 422)

    def test_upload_profile_configure_compare_and_retrieve(self) -> None:
        client = TestClient(app)
        dataframe = _classification_dataframe()
        csv_bytes = dataframe.to_csv(index=False).encode("utf-8")
        uploaded = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("phase_8.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(uploaded.status_code, 200)
        dataset_id = uploaded.json()["dataset"]["dataset_id"]

        self.assertEqual(
            client.post(f"/api/v1/datasets/{dataset_id}/profile").status_code, 200
        )
        configured = client.post(
            f"/api/v1/datasets/{dataset_id}/configuration",
            json={"business_objective": "predict_behavior", "target_column": "churn"},
        )
        self.assertEqual(configured.status_code, 200)
        self.assertEqual(configured.json()["configuration"]["problem_type"], "classification")

        compared = client.post(
            f"/api/v1/datasets/{dataset_id}/experiments/compare",
            json={"runs": 1, "experiment_name": "pytest-api"},
        )
        self.assertEqual(compared.status_code, 200, compared.text)
        body = compared.json()
        self.assertIn("experiment_id", body)
        self.assertIn("comparison", body)
        self.assertEqual(body["comparison"]["performance"]["metric"], "f1")
        self.assertIn("peak_python_memory_mb", body["baseline"]["resources"])
        self.assertIn("peak_python_memory_mb", body["awof"]["resources"])

        experiment_id = body["experiment_id"]
        retrieved = client.get(f"/api/v1/experiments/{experiment_id}")
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.json()["experiment_id"], experiment_id)
        history = client.get(f"/api/v1/datasets/{dataset_id}/experiments")
        self.assertEqual(history.status_code, 200)
        matching = next(item for item in history.json() if item["experiment_id"] == experiment_id)
        self.assertEqual(matching["runs"], 1)


if __name__ == "__main__":
    unittest.main()
