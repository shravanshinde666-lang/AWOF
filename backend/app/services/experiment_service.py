"""Fresh, repeatable fixed-baseline versus AWOF research experiments."""

from __future__ import annotations

import csv
import json
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import matplotlib
import numpy as np
import pandas as pd
import sklearn

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from experiments.adaptive.awof_pipeline import run_awof_pipeline
from experiments.baseline.fixed_pipeline import run_fixed_pipeline

from ..config.settings import BACKEND_DIR
from ..database import repository
from .configuration_service import ConfigurationNotFoundError, get_saved_configuration
from .dataset_service import DatasetNotFoundError, get_dataset, get_profile, load_dataset_dataframe


PROJECT_ROOT = BACKEND_DIR.parent
METRICS_DIR = PROJECT_ROOT / "experiments" / "results" / "metrics"
CHARTS_DIR = PROJECT_ROOT / "experiments" / "results" / "charts"
REPORTS_DIR = PROJECT_ROOT / "experiments" / "results" / "reports"
SUMMARY_PATH = PROJECT_ROOT / "experiments" / "results" / "summary.csv"


class ExperimentPrerequisiteError(Exception):
    pass


class ExperimentNotFoundError(Exception):
    pass


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Unsupported experiment value: {type(value).__name__}")


def _ensure_directories() -> None:
    for directory in (METRICS_DIR, CHARTS_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _mean_std(values: list[Any]) -> dict[str, float | None]:
    numeric = [float(value) for value in values if value is not None]
    if not numeric:
        return {"mean": None, "std": None}
    return {"mean": round(statistics.mean(numeric), 6), "std": round(statistics.stdev(numeric) if len(numeric) > 1 else 0.0, 6)}


def _aggregate_pipeline(runs: list[dict[str, Any]]) -> dict[str, Any]:
    first = json.loads(json.dumps(runs[0], default=_json_default))
    first.pop("run_index", None)
    timing_keys = set().union(*(run.get("timings_ms", {}).keys() for run in runs))
    resource_keys = set().union(*(run.get("resources", {}).keys() for run in runs))
    timing_statistics = {key: _mean_std([run.get("timings_ms", {}).get(key) for run in runs]) for key in timing_keys}
    resource_statistics = {key: _mean_std([run.get("resources", {}).get(key) for run in runs]) for key in resource_keys}
    first["timings_ms"] = {key: values["mean"] or 0.0 for key, values in timing_statistics.items()}
    first["resources"] = {key: values["mean"] or 0.0 for key, values in resource_statistics.items()}
    first["run_statistics"] = {"timings_ms": timing_statistics, "resources": resource_statistics}
    for group in ("workflow_modules", "models"):
        keys = set().union(*(run.get(group, {}).keys() for run in runs))
        for key in keys:
            values = [run.get(group, {}).get(key) for run in runs]
            if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values if value is not None):
                stats = _mean_std(values)
                first[group][key] = int(round(stats["mean"] or 0.0))
    return first


def _safe_percentage(numerator: float, denominator: float, label: str, warnings: list[str]) -> float | None:
    if denominator == 0:
        warnings.append(f"{label} percentage is unavailable because the baseline denominator is zero.")
        return None
    return round(numerator / denominator * 100, 6)


def _primary_metric(problem_type: str, result: dict[str, Any]) -> tuple[str, float | None, str]:
    metric = {"classification": "f1", "regression": "rmse", "clustering": "silhouette_score"}.get(problem_type, "primary_metric")
    direction = "higher_is_better" if problem_type in {"classification", "clustering"} else "lower_is_better"
    value = result.get("best_metrics", {}).get(metric)
    return metric, None if value is None else float(value), direction


def _comparison(problem_type: str, baseline: dict[str, Any], adaptive: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    baseline_modules = float(baseline["workflow_modules"].get("executed", 0))
    awof_modules = float(adaptive["workflow_modules"].get("executed", 0))
    baseline_models = float(baseline["models"].get("trained", 0))
    awof_models = float(adaptive["models"].get("trained", 0))
    baseline_time = float(baseline["timings_ms"].get("overall", 0))
    adaptive_time = float(adaptive["timings_ms"].get("overall", 0))
    baseline_memory = float(baseline["resources"].get("peak_python_memory_mb", 0))
    adaptive_memory = float(adaptive["resources"].get("peak_python_memory_mb", 0))
    module_difference = baseline_modules - awof_modules
    model_difference = baseline_models - awof_models
    time_difference = baseline_time - adaptive_time
    memory_difference = baseline_memory - adaptive_memory
    metric, baseline_metric, direction = _primary_metric(problem_type, baseline)
    _, adaptive_metric, _ = _primary_metric(problem_type, adaptive)
    performance_difference = None if baseline_metric is None or adaptive_metric is None else round(adaptive_metric - baseline_metric, 6)
    statements = [
        f"AWOF executed {abs(module_difference):.0f} {'fewer' if module_difference >= 0 else 'more'} modules than the fixed pipeline.",
        f"AWOF trained {abs(model_difference):.0f} {'fewer' if model_difference >= 0 else 'more'} models than the fixed pipeline.",
        f"Mean runtime difference (baseline minus AWOF) was {time_difference:.3f} ms.",
    ]
    if performance_difference is not None:
        statements.append(f"{metric} difference (AWOF minus baseline) was {performance_difference:.6f} ({direction}).")
    return {
        "module_reduction_count": round(module_difference, 6),
        "module_reduction_percentage": _safe_percentage(module_difference, baseline_modules, "Module reduction", warnings),
        "model_reduction_count": round(model_difference, 6),
        "model_reduction_percentage": _safe_percentage(model_difference, baseline_models, "Model reduction", warnings),
        "execution_time_difference_ms": round(time_difference, 6),
        "execution_time_reduction_percentage": _safe_percentage(time_difference, baseline_time, "Execution-time reduction", warnings),
        "memory_difference_mb": round(memory_difference, 6),
        "memory_reduction_percentage": _safe_percentage(memory_difference, baseline_memory, "Memory reduction", warnings),
        "performance": {"metric": metric, "baseline": baseline_metric, "awof": adaptive_metric, "difference": performance_difference, "direction": f"awof_{metric}_minus_baseline_{metric}"},
        "factual_statements": statements,
        "warnings": warnings,
    }


def _chart(experiment_id: str, filename: str, title: str, baseline: float | None, adaptive: float | None, unit: str) -> None:
    directory = CHARTS_DIR / experiment_id
    directory.mkdir(parents=True, exist_ok=True)
    values = [0.0 if baseline is None else baseline, 0.0 if adaptive is None else adaptive]
    figure, axis = plt.subplots(figsize=(5, 3.2))
    bars = axis.bar(["Fixed", "AWOF"], values, color=["#64748b", "#2563eb"])
    axis.set_title(title)
    axis.set_ylabel(unit)
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.4g}", ha="center", va="bottom")
    figure.tight_layout()
    figure.savefig(directory / filename, dpi=140)
    plt.close(figure)


def _write_charts(result: dict[str, Any]) -> None:
    experiment_id = result["experiment_id"]
    baseline, adaptive = result["baseline"], result["awof"]
    _chart(experiment_id, "execution_time.png", "Mean Execution Time", baseline["timings_ms"].get("overall"), adaptive["timings_ms"].get("overall"), "ms")
    _chart(experiment_id, "memory_usage.png", "Mean Peak Python Memory", baseline["resources"].get("peak_python_memory_mb"), adaptive["resources"].get("peak_python_memory_mb"), "MB")
    _chart(experiment_id, "module_count.png", "Executed Workflow Modules", baseline["workflow_modules"].get("executed"), adaptive["workflow_modules"].get("executed"), "modules")
    _chart(experiment_id, "model_count.png", "Trained Models", baseline["models"].get("trained"), adaptive["models"].get("trained"), "models")
    performance = result["comparison"]["performance"]
    _chart(experiment_id, "performance_comparison.png", f"Primary Performance: {performance['metric']}", performance["baseline"], performance["awof"], performance["metric"])


def _write_report(result: dict[str, Any]) -> None:
    comparison = result["comparison"]
    content = f"""# AWOF Research Experiment: {result['experiment_id']}

## Dataset

- Dataset: {result['dataset_name']}
- Objective: {result['objective']}
- Problem type: {result['problem_type']}
- Target: {result['target'] or 'None'}

## Experimental Setup

Both pipelines used fresh model instances, the same configured target, a deterministic random state of {result['metadata']['random_state']}, and {result['metadata']['runs']} repeated runs. Supervised training uses the same leakage-safe split policy.

## Baseline Workflow

- Executed modules: {result['baseline']['workflow_modules'].get('executed')}
- Trained models: {result['baseline']['models'].get('trained')}
- Best model: {result['baseline'].get('best_model')}

## AWOF Workflow

- Executed modules: {result['awof']['workflow_modules'].get('executed')}
- Pruned modules: {result['awof']['workflow_modules'].get('pruned', 0)}
- Trained models: {result['awof']['models'].get('trained')}
- Best model: {result['awof'].get('best_model')}

## Metrics

- Baseline mean runtime: {result['baseline']['timings_ms'].get('overall')} ms
- AWOF mean runtime: {result['awof']['timings_ms'].get('overall')} ms
- Baseline peak Python memory: {result['baseline']['resources'].get('peak_python_memory_mb')} MB
- AWOF peak Python memory: {result['awof']['resources'].get('peak_python_memory_mb')} MB

## Comparison

""" + "\n".join(f"- {statement}" for statement in comparison["factual_statements"]) + """

## Observed Results

Results are descriptive measurements from this configured dataset and run count. They do not establish statistical significance.

## Limitations

Runtime depends on hardware and warm caches, repeated-run counts may be small, peak memory is Python-tracked memory rather than total machine memory, and ACSA/AMRA heuristics plus dataset characteristics influence outcomes.
"""
    (REPORTS_DIR / f"{result['experiment_id']}.md").write_text(content, encoding="utf-8")


def _write_summary(result: dict[str, Any]) -> None:
    path = SUMMARY_PATH
    performance = result["comparison"]["performance"]
    row = {
        "experiment_id": result["experiment_id"], "dataset_name": result["dataset_name"], "problem_type": result["problem_type"],
        "baseline_modules": result["baseline"]["workflow_modules"].get("executed"), "awof_modules": result["awof"]["workflow_modules"].get("executed"),
        "baseline_models": result["baseline"]["models"].get("trained"), "awof_models": result["awof"]["models"].get("trained"),
        "baseline_time_ms": result["baseline"]["timings_ms"].get("overall"), "awof_time_ms": result["awof"]["timings_ms"].get("overall"),
        "baseline_memory_mb": result["baseline"]["resources"].get("peak_python_memory_mb"), "awof_memory_mb": result["awof"]["resources"].get("peak_python_memory_mb"),
        "primary_metric": performance["metric"], "baseline_primary_metric": performance["baseline"], "awof_primary_metric": performance["awof"],
    }
    with path.open("a", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(row))
        if output.tell() == 0:
            writer.writeheader()
        writer.writerow(row)


def _persist(result: dict[str, Any]) -> None:
    _ensure_directories()
    (METRICS_DIR / f"{result['experiment_id']}.json").write_text(json.dumps(result, indent=2, default=_json_default), encoding="utf-8")
    _write_summary(result)
    _write_report(result)
    _write_charts(result)


def _metadata(runs: int, configuration: dict[str, Any]) -> dict[str, Any]:
    return {
        "runs": runs, "random_state": 42, "model_registry_version": "AMRA-1.0", "acsa_version": "ACSA-1.0", "awga_version": "AWGA-1.0", "amra_version": "AMRA-1.0",
        "software_versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "memory_measurement": "Peak Python allocations measured with tracemalloc; not total machine RAM.",
        "configuration": {
            "problem_type": configuration.get("problem_type"),
            "business_objective": (configuration.get("business_objective") or {}).get("id"),
            "target_column": (configuration.get("target") or {}).get("column"),
        },
    }


def run_comparison(dataset_id: str, runs: int = 3, experiment_name: str | None = None) -> dict[str, Any]:
    if not 1 <= runs <= 10:
        raise ExperimentPrerequisiteError("Runs must be between 1 and 10.")
    try:
        metadata = get_dataset(dataset_id)
        profile = get_profile(dataset_id)
        configuration = get_saved_configuration(dataset_id)
        dataframe = load_dataset_dataframe(dataset_id)
    except (ConfigurationNotFoundError, DatasetNotFoundError) as exc:
        raise ExperimentPrerequisiteError("A dataset, generated profile, and valid saved configuration are required before a research experiment.") from exc
    if not configuration.get("valid"):
        raise ExperimentPrerequisiteError("The saved analysis configuration is invalid.")
    baseline_runs: list[dict[str, Any]] = []
    adaptive_runs: list[dict[str, Any]] = []
    for run_index in range(1, runs + 1):
        # Alternating within every repeat minimizes systematic all-baseline-first cache bias.
        baseline_run = dict(run_fixed_pipeline(
            dataframe.copy(deep=True), configuration, profile,
            random_state=42, experiment_name=experiment_name,
        ))
        adaptive_run = dict(run_awof_pipeline(
            dataframe.copy(deep=True), configuration, profile,
            random_state=42, experiment_name=experiment_name,
        ))
        baseline_run["run_index"] = run_index
        adaptive_run["run_index"] = run_index
        baseline_runs.append(baseline_run)
        adaptive_runs.append(adaptive_run)
    baseline = _aggregate_pipeline(baseline_runs)
    adaptive = _aggregate_pipeline(adaptive_runs)
    experiment_id = str(uuid4())
    comparison = _comparison(configuration["problem_type"], baseline, adaptive)
    result = {
        "experiment_id": experiment_id, "dataset_id": dataset_id, "dataset_name": metadata.original_filename,
        "problem_type": configuration["problem_type"], "objective": configuration["business_objective"]["id"],
        "target": (configuration.get("target") or {}).get("column"), "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": _metadata(runs, configuration), "baseline": baseline, "awof": adaptive, "comparison": comparison,
        "run_results": {"baseline": baseline_runs, "awof": adaptive_runs},
        "warnings": [*comparison["warnings"], "Repeated timing is descriptive and may be affected by operating-system filesystem caching."],
    }
    _persist(result)
    try:
        repository.save_experiment(experiment_id, dataset_id, result)
    except repository.PersistenceNotFoundError as exc:
        raise ExperimentPrerequisiteError("The dataset is no longer available for experiment persistence.") from exc
    return result


def _safe_experiment_id(experiment_id: str) -> str:
    safe = Path(experiment_id).name
    if safe != experiment_id or not safe:
        raise ExperimentNotFoundError("Experiment not found.")
    return safe


def get_experiment(experiment_id: str) -> dict[str, Any]:
    experiment_id = _safe_experiment_id(experiment_id)
    try:
        return repository.get_experiment(experiment_id)
    except repository.PersistenceNotFoundError as exc:
        raise ExperimentNotFoundError("Experiment not found.") from exc


def get_dataset_experiments(dataset_id: str) -> list[dict[str, Any]]:
    try:
        repository.get_dataset(dataset_id)
        stored = repository.list_experiments(dataset_id)
    except repository.PersistenceNotFoundError as exc:
        raise ExperimentNotFoundError("Dataset not found.") from exc
    values: list[dict[str, Any]] = []
    for result in stored:
        summary = {key: result.get(key) for key in ("experiment_id", "dataset_id", "dataset_name", "problem_type", "objective", "timestamp")}
        summary["runs"] = int(result.get("metadata", {}).get("runs", 1))
        values.append(summary)
    return values
