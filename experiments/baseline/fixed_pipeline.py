"""Reasonable, deterministic conventional baseline for Phase 8 research.

The baseline trains every *available* Phase 6 registry model compatible with
the configured task.  It deliberately shares Phase 6 fitted preprocessing and
its split policy with AWOF so differences measure selection strategy rather
than a weaker or leakage-prone implementation.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import pandas as pd

from awof.profiler import DatasetProfiler

from experiments._common import (
    all_compatible_recommendation,
    attach_resources,
    base_result,
    dataset_identifier,
    effective_random_state,
    fixed_workflow_execution,
    measure_entire_run,
    model_summary,
    remove_exact_duplicates,
    split_metadata,
    train_models,
    validate_inputs,
)


def run_fixed_pipeline(
    dataframe: pd.DataFrame,
    configuration: dict[str, Any],
    profile: dict[str, Any] | None,
    random_state: int = 42,
    experiment_name: str | None = None,
) -> dict[str, Any]:
    """Run the fair fixed baseline once and return a JSON-safe research record.

    The input frame is never modified.  For supervised tasks, exact duplicate
    removal is applied equally to both Phase 8 arms and all learned operations
    are fitted inside Phase 6 pipelines after the deterministic train/test
    split.  XGBoost stays excluded when its registry entry is unavailable.
    """

    validate_inputs(dataframe, configuration)
    effective_state, state_warnings = effective_random_state(random_state)

    def operation() -> dict[str, Any]:
        overall_started = perf_counter()
        profiling_started = perf_counter()
        fresh_profile = DatasetProfiler(
            dataframe.copy(deep=True),
            dataset_identifier(configuration),
        ).generate_profile()
        profiling_ms = round((perf_counter() - profiling_started) * 1_000, 3)
        prep_started = perf_counter()
        comparable_dataframe, duplicate_info = remove_exact_duplicates(dataframe)
        preprocessing_ms = round((perf_counter() - prep_started) * 1_000, 3)
        execution_started = perf_counter()
        execution, modules = fixed_workflow_execution(
            dataframe, configuration, fresh_profile, duplicate_info,
        )
        execution_ms = round((perf_counter() - execution_started) * 1_000, 3)
        recommendation = all_compatible_recommendation(configuration)
        training_result, pipelines, training_timings = train_models(
            comparable_dataframe, configuration, recommendation, fresh_profile,
        )
        model_info = model_summary(recommendation, training_result, pipelines, configuration["problem_type"])
        timings = {
            "profiling": profiling_ms,
            "configuration_acsa_awga": 0.0,
            "preprocessing": preprocessing_ms,
            "pruning": 0.0,
            "execution": execution_ms,
            "model_recommendation": 0.0,
            **training_timings,
            "overall": round((perf_counter() - overall_started) * 1_000, 3),
        }
        warnings = [
            *state_warnings,
            "Baseline preprocessing uses the same Phase 6 train-fitted imputation, encoding, and scaling implementation as AWOF.",
            "Evaluation timing is included in model_training because Phase 6 evaluates each model within its training transaction.",
        ]
        result = base_result(
            pipeline_name="fixed_baseline",
            configuration=configuration,
            random_state=effective_state,
            split=split_metadata(comparable_dataframe, configuration, effective_state),
            module_ids=modules,
            pruned_module_ids=[],
            model_info=model_info,
            timings=timings,
            warnings=warnings,
            experiment_name=experiment_name,
        )
        result["baseline_modules_considered"] = result["workflow_modules"]["considered"]
        result["baseline_modules_executed"] = result["workflow_modules"]["executed"]
        result["preparation"] = duplicate_info
        result["execution"] = execution
        result["model_recommendation"] = recommendation
        return result

    result, resources = measure_entire_run(operation)
    return attach_resources(result, resources)
