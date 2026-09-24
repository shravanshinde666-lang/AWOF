import unittest

import pandas as pd

from awof.acsa import ACSAScorer
from awof.acsa.thresholds import decision_for
from awof.configuration.configuration import build_configuration
from awof.profiler import DatasetProfiler


def capability(result, capability_id):
    return next(item for item in result["capabilities"] if item["id"] == capability_id)


class ACSATests(unittest.TestCase):
    def profile_and_config(self, dataframe, objective="predict_behavior", target="target"):
        profile = DatasetProfiler(dataframe, dataset_id="test").generate_profile()
        configuration = build_configuration("test", objective, target, profile)
        return profile, configuration

    def test_decision_thresholds(self):
        self.assertEqual(decision_for(.80), "run")
        self.assertEqual(decision_for(.55), "optional")
        self.assertEqual(decision_for(.20), "skip")

    def test_missing_score_increases(self):
        clean, clean_config = self.profile_and_config(pd.DataFrame({"value": [1, 2, 3], "target": ["a", "b", "a"]}))
        missing, missing_config = self.profile_and_config(pd.DataFrame({"value": [1, None, None, None], "target": ["a", "b", "a", "b"]}))
        self.assertLess(capability(ACSAScorer(clean, clean_config).generate(), "missing_value_handling")["score"], capability(ACSAScorer(missing, missing_config).generate(), "missing_value_handling")["score"])

    def test_text_and_encoding_signals(self):
        profile, configuration = self.profile_and_config(pd.DataFrame({"notes": ["customer described a detailed account concern today", "customer wrote a lengthy renewal feedback message", "customer shared a detailed service experience note"], "kind": ["x", "y", "x"], "target": ["a", "b", "a"]}))
        result = ACSAScorer(profile, configuration).generate()
        self.assertGreater(capability(result, "text_analysis")["score"], 0)
        self.assertGreater(capability(result, "encoding")["score"], 0)

    def test_classification_imbalance_and_model_scores(self):
        dataframe = pd.DataFrame({"feature": list(range(20)), "target": ["no"] * 19 + ["yes"]})
        profile, configuration = self.profile_and_config(dataframe)
        result = ACSAScorer(profile, configuration, dataframe).generate()
        self.assertEqual(capability(result, "classification")["decision"], "run")
        self.assertEqual(capability(result, "regression")["decision"], "skip")
        self.assertEqual(capability(result, "imbalance_handling")["decision"], "run")

    def test_regression_and_segmentation(self):
        regression_df = pd.DataFrame({"feature": [1, 2, 3, 4], "target": [10.1, 12.4, 15.8, 18.6]})
        profile, configuration = self.profile_and_config(regression_df)
        self.assertEqual(capability(ACSAScorer(profile, configuration, regression_df).generate(), "regression")["decision"], "run")
        cluster_profile, cluster_config = self.profile_and_config(regression_df, "segment_customers", None)
        self.assertEqual(capability(ACSAScorer(cluster_profile, cluster_config, regression_df).generate(), "clustering")["decision"], "run")

    def test_deterministic_scores(self):
        dataframe = pd.DataFrame({"category": ["a", "b", "a"], "target": ["yes", "no", "yes"]})
        profile, configuration = self.profile_and_config(dataframe)
        first = ACSAScorer(profile, configuration, dataframe).generate()
        second = ACSAScorer(profile, configuration, dataframe).generate()
        self.assertEqual([(item["id"], item["score"], item["decision"]) for item in first["capabilities"]], [(item["id"], item["score"], item["decision"]) for item in second["capabilities"]])
