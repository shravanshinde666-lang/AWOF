import unittest

import numpy as np
import pandas as pd

from awof.ml.evaluator import classification_metrics
from awof.profiler import DatasetProfiler
from backend.app.services.dataset_service import normalize_dataframe
from backend.app.services.insight_service import _feature_target_ranking


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

    def test_profile_reports_aggregated_missingness_patterns_without_rows(self) -> None:
        dataframe = pd.DataFrame({
            "income": [100.0, None, None, 400.0],
            "tenure": [1.0, None, None, 4.0],
            "segment": ["a", "b", None, "d"],
        })
        profile = DatasetProfiler(dataframe).generate_profile()
        patterns = profile["quality"]["missing_values"]["patterns"]
        self.assertEqual(patterns["distinct_patterns"], 2)
        self.assertEqual(patterns["patterns"][0]["columns"], ["income", "tenure"])
        self.assertEqual(patterns["patterns"][0]["row_count"], 1)

    def test_mutual_information_ranks_numeric_features_for_a_configured_target(self) -> None:
        dataframe = pd.DataFrame({
            "signal": [0.0, 0.1, 0.9, 1.0, 0.2, 0.8, 0.3, 0.7],
            "noise": [4, 1, 8, 2, 7, 3, 6, 5],
            "target": ["no", "no", "yes", "yes", "no", "yes", "no", "yes"],
        })
        profile = DatasetProfiler(dataframe).generate_profile()
        ranking = _feature_target_ranking(dataframe, profile, "target", "classification")
        self.assertEqual(ranking["method"], "mutual_information")
        self.assertEqual(ranking["items"][0]["feature"], "signal")
        self.assertGreater(ranking["items"][0]["score"], 0)
