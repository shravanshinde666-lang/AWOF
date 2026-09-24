import unittest

import pandas as pd
from sklearn.pipeline import Pipeline

from awof.amra import AMRARecommender
from awof.ml.trainer import build_supervised_pipeline, select_best_model, train_recommended_models
from tests.test_amra import configuration, execution, profile_for


class MachineLearningTests(unittest.TestCase):
    def _recommendation(self, dataframe: pd.DataFrame, problem_type: str, target: str | None = None) -> dict:
        return AMRARecommender().recommend(profile_for(dataframe, target), configuration(problem_type, target), execution(len(dataframe)), dataframe)

    def test_classification_training_metrics_and_cross_validation(self) -> None:
        data = pd.DataFrame({"identifier": [f"r{index}" for index in range(40)], "x": list(range(40)), "group": ["a", "b"] * 20, "target": ["no"] * 20 + ["yes"] * 20})
        result, _ = train_recommended_models(data, configuration("classification", "target"), self._recommendation(data, "classification", "target"), profile_for(data, "target"))
        completed = [item for item in result["results"] if item["status"] == "completed"]
        self.assertTrue(completed)
        for metric in ("accuracy", "precision", "recall", "f1"):
            self.assertIn(metric, completed[0]["test_metrics"])
        self.assertTrue(completed[0]["cross_validation_metrics"])

    def test_regression_training_metrics(self) -> None:
        data = pd.DataFrame({"x": list(range(50)), "category": ["a", "b"] * 25, "target": [index * 2.5 + 1 for index in range(50)]})
        result, _ = train_recommended_models(data, configuration("regression", "target"), self._recommendation(data, "regression", "target"), profile_for(data, "target"))
        completed = next(item for item in result["results"] if item["status"] == "completed")
        self.assertTrue({"mae", "rmse", "r2"}.issubset(completed["test_metrics"]))

    def test_clustering_training_generates_labels_and_quality_metric(self) -> None:
        data = pd.DataFrame({"x": [0, .1, -.1, .2, 10, 10.1, 9.9, 10.2, 20, 20.1, 19.9, 20.2], "y": [0, .2, .1, -.1, 10, 9.9, 10.2, 10.1, 20, 19.8, 20.1, 20.2]})
        recommendation = self._recommendation(data, "clustering")
        result, _ = train_recommended_models(data, configuration("clustering"), recommendation, profile_for(data))
        completed = [item for item in result["results"] if item["status"] == "completed"]
        self.assertTrue(completed)
        self.assertTrue(any("cluster_labels" in item for item in completed))
        self.assertTrue(any(item["test_metrics"].get("silhouette_score") is not None for item in completed))

    def test_supervised_preprocessing_is_an_unfitted_pipeline(self) -> None:
        data = pd.DataFrame({"x": list(range(20)), "category": ["a", "b"] * 10})
        pipeline = build_supervised_pipeline(data, "logistic_regression")
        self.assertIsInstance(pipeline, Pipeline)
        self.assertIn("preprocessor", pipeline.named_steps)
        self.assertNotIn("transformers_", pipeline.named_steps["preprocessor"].__dict__)

    def test_model_failure_isolated_from_other_recommended_models(self) -> None:
        data = pd.DataFrame({"x": list(range(30)), "target": ["no"] * 15 + ["yes"] * 15})
        recommendation = {"models": [{"model_id": "logistic_regression", "decision": "recommended", "available": True}, {"model_id": "does_not_exist", "decision": "recommended", "available": True}]}
        result, _ = train_recommended_models(data, configuration("classification", "target"), recommendation, profile_for(data, "target"))
        statuses = {item["model_id"]: item["status"] for item in result["results"]}
        self.assertEqual(statuses["does_not_exist"], "failed")
        self.assertEqual(statuses["logistic_regression"], "completed")

    def test_best_model_metric_rules(self) -> None:
        classification = select_best_model([{"model_id": "a", "status": "completed", "test_metrics": {"f1": .7, "roc_auc": .8}}, {"model_id": "b", "status": "completed", "test_metrics": {"f1": .8, "roc_auc": .7}}], "classification")
        regression = select_best_model([{"model_id": "a", "status": "completed", "test_metrics": {"rmse": 2, "r2": .9}}, {"model_id": "b", "status": "completed", "test_metrics": {"rmse": 1, "r2": .5}}], "regression")
        clustering = select_best_model([{"model_id": "a", "status": "completed", "test_metrics": {"silhouette_score": .3}}, {"model_id": "b", "status": "completed", "test_metrics": {"silhouette_score": .6}}], "clustering")
        self.assertEqual((classification or {})["model_id"], "b")
        self.assertEqual((regression or {})["model_id"], "b")
        self.assertEqual((clustering or {})["model_id"], "b")
