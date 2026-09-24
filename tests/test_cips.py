import unittest

import numpy as np
import pandas as pd

from awof.cips import calculate_cips, detect_business_signals, priority_level
from backend.app.services.business_service import _classification_risk, _not_applicable
from awof.ml.trainer import build_supervised_pipeline


class CIPSTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = pd.DataFrame({"customer_id": ["c1", "c2", "c3", "c4"], "monthly_spend": [20, 100, 60, 200], "support_tickets": [0, 1, 3, 2]})
        self.predictions = np.array(["no", "yes", "yes", "yes"])
        self.risk = np.array([.1, .7, .8, .95])

    def test_scores_are_bounded_and_ranked(self) -> None:
        mapping, _ = detect_business_signals(self.data)
        rows, _, _ = calculate_cips(self.data, self.predictions, self.risk, mapping, "customer_id", "analyze_retention")
        self.assertTrue(all(0 <= row["cips_score"] <= 100 for row in rows))
        self.assertEqual(rows, sorted(rows, key=lambda row: (-row["cips_score"], row["row_index"])))

    def test_effective_weights_are_normalized(self) -> None:
        mapping, _ = detect_business_signals(self.data)
        _, weights, _ = calculate_cips(self.data, self.predictions, self.risk, mapping, "customer_id", "analyze_retention")
        self.assertAlmostEqual(sum(weights.values()), 1.0)

    def test_risk_only_priority_is_still_supported(self) -> None:
        rows, weights, _ = calculate_cips(self.data, self.predictions, self.risk, {}, "customer_id", "analyze_retention")
        self.assertEqual(weights, {"risk": 1.0})
        self.assertGreater(rows[0]["cips_score"], rows[-1]["cips_score"])

    def test_priority_thresholds(self) -> None:
        self.assertEqual(priority_level(85), "immediate")
        self.assertEqual(priority_level(70), "high")
        self.assertEqual(priority_level(40), "medium")
        self.assertEqual(priority_level(39.99), "monitor")

    def test_segmentation_is_not_applicable(self) -> None:
        result = _not_applicable("cluster", "clustering", "not applicable")
        self.assertEqual(result["applicability"], "not_applicable")
        self.assertFalse(result["items"])

    def test_risk_direction_is_explicit_for_churn_and_retention_targets(self) -> None:
        features = pd.DataFrame({"x": list(range(30))})
        labels = pd.Series(["no"] * 15 + ["yes"] * 15)
        pipeline = build_supervised_pipeline(features, "logistic_regression")
        pipeline.fit(features, labels)
        churn_config = {"target": {"column": "churn"}, "business_objective": {"id": "analyze_retention"}}
        retained_config = {"target": {"column": "retained"}, "business_objective": {"id": "analyze_retention"}}
        _, churn_risk, churn_direction, _ = _classification_risk(pipeline, features, churn_config)
        _, retained_risk, retained_direction, _ = _classification_risk(pipeline, features, retained_config)
        self.assertEqual(churn_direction, "positive_risk_probability")
        self.assertEqual(retained_direction, "inverted_retention_probability")
        self.assertAlmostEqual(float(churn_risk[0] + retained_risk[0]), 1.0, places=6)
