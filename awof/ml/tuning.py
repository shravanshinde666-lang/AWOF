"""Bounded, leakage-safe hyperparameter tuning helpers."""

from __future__ import annotations

from typing import Any

from sklearn.model_selection import RandomizedSearchCV


PARAMETERS: dict[str, dict[str, list[Any]]] = {
    "logistic_regression": {"model__C": [0.01, 0.1, 1.0, 10.0, 100.0]},
    "ridge_regression": {"model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
    "random_forest_classifier": {"model__n_estimators": [100, 200, 300], "model__max_depth": [None, 5, 10], "model__min_samples_leaf": [1, 2, 4]},
    "random_forest_regressor": {"model__n_estimators": [100, 200, 300], "model__max_depth": [None, 5, 10], "model__min_samples_leaf": [1, 2, 4]},
    "gradient_boosting_classifier": {"model__n_estimators": [50, 100, 200], "model__learning_rate": [0.03, 0.1, 0.2], "model__max_depth": [2, 3, 4]},
    "gradient_boosting_regressor": {"model__n_estimators": [50, 100, 200], "model__learning_rate": [0.03, 0.1, 0.2], "model__max_depth": [2, 3, 4]},
}


def scoring_for(problem_type: str) -> str:
    return "f1_weighted" if problem_type == "classification" else "neg_root_mean_squared_error"


def tune_pipeline(pipeline: Any, features: Any, target: Any, model_id: str, problem_type: str) -> tuple[Any, dict[str, Any]]:
    parameters = PARAMETERS.get(model_id)
    if not parameters:
        raise ValueError(f"Tuning is not configured for '{model_id}'.")
    search = RandomizedSearchCV(
        pipeline, parameters, n_iter=min(8, max(len(values) for values in parameters.values()) ** len(parameters)),
        scoring=scoring_for(problem_type), cv=3, random_state=42, n_jobs=1, refit=True,
    )
    search.fit(features, target)
    return search.best_estimator_, {"best_parameters": search.best_params_, "cross_validation_score": float(search.best_score_), "scoring": scoring_for(problem_type), "candidates_evaluated": len(search.cv_results_["params"])}
