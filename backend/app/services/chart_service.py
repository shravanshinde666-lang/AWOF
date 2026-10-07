"""Generate durable, data-backed visual artifacts for completed model evaluations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ..config.settings import BACKEND_DIR


def _directory() -> Path:
    path = BACKEND_DIR.parent / "storage" / "charts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _metric(problem_type: str) -> tuple[str, str]:
    if problem_type == "classification":
        return "f1", "F1 score"
    if problem_type == "regression":
        return "rmse", "RMSE (lower is better)"
    return "silhouette_score", "Silhouette score"


def create_evaluation_charts(dataset_id: str, evaluation: dict[str, Any]) -> dict[str, str]:
    """Write compact PNG charts from actual evaluation output and return public URLs."""
    problem_type = str(evaluation["problem_type"])
    metric_key, metric_label = _metric(problem_type)
    completed = [item for item in evaluation.get("results", []) if item.get("status") == "completed"]
    if not completed:
        return {}

    output = _directory()
    labels = [str(item["model_id"]).replace("_", " ").title() for item in completed]
    values = [float(item.get("test_metrics", {}).get(metric_key) or 0) for item in completed]
    figure, axis = plt.subplots(figsize=(8, 4.2), dpi=150)
    bars = axis.barh(labels, values, color="#1d67dd")
    axis.set_title(f"Model comparison — {metric_label}", loc="left", fontweight="bold")
    axis.set_xlabel(metric_label)
    axis.grid(axis="x", alpha=0.2)
    axis.set_axisbelow(True)
    for bar, value in zip(bars, values):
        axis.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f"  {value:.3f}", va="center", fontsize=9)
    figure.tight_layout()
    comparison_name = f"{dataset_id}_model_comparison.png"
    figure.savefig(output / comparison_name, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    charts = {"comparison": f"/artifacts/charts/{comparison_name}"}

    best = evaluation.get("best_model") or {}
    best_result = next((item for item in completed if item.get("model_id") == best.get("model_id")), None)
    matrix = best_result and best_result.get("test_metrics", {}).get("confusion_matrix")
    if problem_type == "classification" and isinstance(matrix, list) and matrix:
        data = np.asarray(matrix)
        figure, axis = plt.subplots(figsize=(4.8, 4.2), dpi=150)
        image = axis.imshow(data, cmap="Blues")
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
        axis.set_title("Best model — confusion matrix", loc="left", fontweight="bold")
        axis.set_xlabel("Predicted class")
        axis.set_ylabel("Actual class")
        for row in range(data.shape[0]):
            for column in range(data.shape[1]):
                axis.text(column, row, str(data[row, column]), ha="center", va="center", color="#10285a", fontweight="bold")
        figure.tight_layout()
        matrix_name = f"{dataset_id}_confusion_matrix.png"
        figure.savefig(output / matrix_name, bbox_inches="tight", facecolor="white")
        plt.close(figure)
        charts["confusion_matrix"] = f"/artifacts/charts/{matrix_name}"
    return charts
