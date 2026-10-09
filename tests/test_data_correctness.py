import unittest

import numpy as np
import pandas as pd

from awof.ml.evaluator import classification_metrics
from awof.profiler import DatasetProfiler
from backend.app.services.dataset_service import normalize_dataframe


class DataCorrectnessTests(unittest.TestCase):
    def test_whitespace_missing_and_numeric_like_are_normalized(self) -> None:
        raw = pd.DataFrame({"customerID": ["a", "b", "c"], "TotalCharges": [" 29.85 ", "   ", "1889.5"]})
        data = normalize_dataframe(raw)
        profile = DatasetProfiler(data).generate_profile()
        total = next(item for item in profile["column_types"] if item["column"] == "TotalCharges")
        self.assertEqual(data["TotalCharges"].isna().sum(), 1)
        self.assertEqual(total["broad_type"], "numerical")
        self.assertEqual(profile["columns"]["TotalCharges"]["missing"]["missing_count"], 1)

    def test_binary_metrics_identify_yes_as_positive_class(self) -> None:
        metrics, _ = classification_metrics(["No", "No", "Yes", "Yes"], ["No", "Yes", "Yes", "Yes"], None)
        self.assertEqual(metrics["positive_class"], "Yes")
        self.assertEqual(metrics["positive_recall"], 1.0)
        self.assertIn("positive_f1", metrics)

    def test_binary_probability_metrics_use_the_semantic_positive_class_column(self) -> None:
        truth = np.array(["churn", "churn", "stay", "stay"])
        predictions = np.array(["churn", "churn", "stay", "stay"])
        # sklearn orders these classes as ["churn", "stay"], so the semantic
        # positive/risk class is column zero rather than the conventional column one.
        probabilities = np.array([[0.90, 0.10], [0.80, 0.20], [0.20, 0.80], [0.10, 0.90]])
        metrics, warnings = classification_metrics(truth, predictions, probabilities)
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["positive_class"], "churn")
        self.assertEqual(metrics["roc_auc"], 1.0)
        self.assertAlmostEqual(metrics["brier_score"], 0.025)
        self.assertIsNotNone(metrics["log_loss"])
