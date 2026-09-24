import unittest

import pandas as pd

from awof.configuration.configuration import build_configuration
from awof.configuration.objectives import OBJECTIVES
from awof.configuration.target_analyzer import analyze_target_candidates
from awof.profiler import DatasetProfiler


class AnalysisConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        dataframe = pd.DataFrame({
            "customer_id": [101, 102, 103, 104, 105],
            "churn": ["No", "Yes", "No", "Yes", "No"],
            "revenue": [10.5, 13.2, 15.0, 18.7, 22.4],
            "constant": ["yes"] * 5,
        })
        self.profile = DatasetProfiler(dataframe, dataset_id="test-dataset").generate_profile()

    def test_all_objectives_and_requirements_exist(self) -> None:
        self.assertEqual(set(OBJECTIVES), {
            "predict_behavior", "segment_customers", "identify_risk",
            "analyze_retention", "optimize_revenue",
        })
        self.assertEqual(OBJECTIVES["segment_customers"].target_requirement, "none")
        self.assertEqual(OBJECTIVES["optimize_revenue"].target_requirement, "optional")

    def test_binary_target_suggests_classification(self) -> None:
        candidate = next(item for item in analyze_target_candidates(self.profile) if item["column"] == "churn")
        self.assertEqual(candidate["suggested_problem_type"], "classification")

    def test_continuous_target_suggests_regression(self) -> None:
        candidate = next(item for item in analyze_target_candidates(self.profile) if item["column"] == "revenue")
        self.assertEqual(candidate["suggested_problem_type"], "regression")

    def test_identifier_is_not_recommended(self) -> None:
        candidate = next(item for item in analyze_target_candidates(self.profile) if item["column"] == "customer_id")
        self.assertEqual(candidate["target_suitability"], "unsuitable")
        self.assertTrue(any("identifier" in reason.lower() for reason in candidate["reasons"]))

    def test_constant_target_is_invalid(self) -> None:
        result = build_configuration("test-dataset", "predict_behavior", "constant", self.profile)
        self.assertFalse(result["valid"])

    def test_all_null_target_is_invalid(self) -> None:
        profile = DatasetProfiler(pd.DataFrame({"missing_target": [None, None, None]})).generate_profile()
        result = build_configuration("test-dataset", "predict_behavior", "missing_target", profile)
        self.assertFalse(result["valid"])

    def test_segmentation_has_no_target(self) -> None:
        result = build_configuration("test-dataset", "segment_customers", None, self.profile)
        self.assertTrue(result["valid"])
        self.assertEqual(result["problem_type"], "clustering")

    def test_retention_requires_target(self) -> None:
        result = build_configuration("test-dataset", "analyze_retention", None, self.profile)
        self.assertFalse(result["valid"])

    def test_revenue_without_target_is_valid(self) -> None:
        result = build_configuration("test-dataset", "optimize_revenue", None, self.profile)
        self.assertTrue(result["valid"])
        self.assertEqual(result["problem_type"], "business_analysis")
