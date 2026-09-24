import unittest

import pandas as pd

from awof.amra import AMRARecommender


def profile_for(dataframe: pd.DataFrame, target: str | None = None, *, high_dimension: bool = False) -> dict:
    types = []
    for column in dataframe.columns:
        broad_type = "numerical" if pd.api.types.is_numeric_dtype(dataframe[column]) else "categorical"
        types.append({"column": column, "broad_type": broad_type, "is_identifier_candidate": False})
    if high_dimension:
        types.extend({"column": f"extra_{index}", "broad_type": "numerical", "is_identifier_candidate": False} for index in range(60))
    return {
        "summary": {"rows": len(dataframe)},
        "column_types": types,
        "correlations": {"pairs": [{"correlation": 0.81}] if high_dimension else []},
    }


def configuration(problem_type: str, target: str | None = None) -> dict:
    return {"dataset_id": "amra-test", "problem_type": problem_type, "target": {"column": target} if target else None}


def execution(rows: int) -> dict:
    return {"summary": {"final_rows": rows}, "node_results": [{"node_id": "scaling", "status": "completed"}]}


class AMRATests(unittest.TestCase):
    def setUp(self) -> None:
        self.classification = pd.DataFrame({"income": list(range(30)), "segment": ["a", "b"] * 15, "target": ["yes", "no"] * 15})

    def test_classification_only_returns_classification_models(self) -> None:
        result = AMRARecommender().recommend(profile_for(self.classification, "target"), configuration("classification", "target"), execution(len(self.classification)), self.classification)
        self.assertEqual({item["model_id"] for item in result["models"]}, {"logistic_regression", "random_forest_classifier", "gradient_boosting_classifier", "xgboost_classifier"})
        self.assertTrue(all(0 <= item["score"] <= 1 for item in result["models"]))
        self.assertTrue(all(item["decision"] == "incompatible" for item in result["incompatible_models"]))

    def test_regression_only_returns_regression_models(self) -> None:
        data = pd.DataFrame({"x": list(range(30)), "y": [value * 2 for value in range(30)]})
        result = AMRARecommender().recommend(profile_for(data, "y"), configuration("regression", "y"), execution(len(data)), data)
        self.assertEqual(
            {item["model_id"] for item in result["models"]},
            {"linear_regression", "ridge_regression", "random_forest_regressor", "gradient_boosting_regressor", "xgboost_regressor"},
        )
        self.assertEqual(result["summary"]["models_recommended"], 3)

    def test_clustering_only_returns_clustering_models(self) -> None:
        data = pd.DataFrame({"x": list(range(20)), "y": list(range(20, 40))})
        result = AMRARecommender().recommend(profile_for(data), configuration("clustering"), execution(len(data)), data)
        self.assertEqual({item["model_id"] for item in result["models"]}, {"kmeans", "dbscan", "agglomerative_clustering"})
        self.assertEqual(result["summary"]["models_recommended"], 2)

    def test_ranking_is_deterministic(self) -> None:
        args = (profile_for(self.classification, "target"), configuration("classification", "target"), execution(len(self.classification)), self.classification)
        self.assertEqual(AMRARecommender().recommend(*args), AMRARecommender().recommend(*args))

    def test_logistic_regression_has_a_non_zero_sensible_score(self) -> None:
        result = AMRARecommender().recommend(profile_for(self.classification, "target"), configuration("classification", "target"), execution(len(self.classification)), self.classification)
        logistic = next(item for item in result["models"] if item["model_id"] == "logistic_regression")
        self.assertGreater(logistic["score"], 0)
        self.assertTrue(logistic["reasons"])

    def test_high_dimensional_regression_favors_ridge_over_plain_linear(self) -> None:
        data = pd.DataFrame({"x": list(range(30)), "y": [value * 2 for value in range(30)]})
        result = AMRARecommender().recommend(profile_for(data, "y", high_dimension=True), configuration("regression", "y"), execution(len(data)), data)
        scores = {item["model_id"]: item["score"] for item in result["models"]}
        self.assertGreater(scores["ridge_regression"], scores["linear_regression"])
