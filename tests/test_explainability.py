import unittest

import pandas as pd

from awof.explainability import global_importance, local_explanation
from awof.ml.trainer import build_supervised_pipeline


class ExplainabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.features = pd.DataFrame({"age": list(range(40)), "contract": ["Month-to-month", "Annual"] * 20})
        self.target = pd.Series(["no"] * 20 + ["yes"] * 20)
        self.classifier = build_supervised_pipeline(self.features, "logistic_regression")
        self.classifier.fit(self.features, self.target)

    def test_global_importance_is_non_empty_with_recovered_feature_names(self) -> None:
        method, items, _ = global_importance(self.classifier, self.features, self.target)
        self.assertEqual(method, "linear_coefficients")
        self.assertTrue(items)
        self.assertTrue(any(item["feature"].startswith("contract_") or item["feature"] == "age" for item in items))
        self.assertFalse(any(item["feature"].startswith("x") and item["feature"][1:].isdigit() for item in items))

    def test_local_explanation_has_prediction_contributions_and_method(self) -> None:
        result, warnings = local_explanation(self.classifier, self.features.iloc[[0]], "classification")
        self.assertIn("prediction", result)
        self.assertIn("prediction_probability", result)
        self.assertTrue(result["feature_contributions"])
        self.assertEqual(result["method"], "linear_coefficients")
        self.assertFalse(warnings)

    def test_tree_fallback_uses_native_importance_when_shap_is_unavailable(self) -> None:
        pipeline = build_supervised_pipeline(self.features, "random_forest_classifier")
        pipeline.fit(self.features, self.target)
        method, items, _ = global_importance(pipeline, self.features, self.target)
        self.assertEqual(method, "native_feature_importance")
        self.assertTrue(items)

    def test_regression_explanation_returns_predicted_value_not_probability(self) -> None:
        target = pd.Series([value * 3.0 + 1 for value in range(40)])
        pipeline = build_supervised_pipeline(self.features, "linear_regression")
        pipeline.fit(self.features, target)
        result, _ = local_explanation(pipeline, self.features.iloc[[0]], "regression")
        self.assertIn("predicted_value", result)
        self.assertNotIn("prediction_probability", result)
