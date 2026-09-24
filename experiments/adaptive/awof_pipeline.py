"""Real AWOF adaptive runner used by the Phase 8 research comparison.

This runner invokes the implemented profiler, configuration builder, ACSA,
AWGA, pruning, execution, AMRA, Phase 6 training, and compact Phase 7 output.
Its primary model metrics still come from a fresh Phase 6 split/fitted pipeline
rather than the Phase 5 full-frame executor, preserving leakage safety.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import pandas as pd

from awof.acsa import ACSAScorer
from awof.amra import AMRARecommender
from awof.awga import AWGAGenerator
from awof.configuration.configuration import build_configuration
from awof.execution.executor import execute
from awof.pruning import prune
from awof.profiler import DatasetProfiler

from experiments._common import (
    CORE_WORKFLOW_NODES,
    attach_resources,
    base_result,
    dataset_identifier,
    effective_random_state,
    json_safe,
    measure_entire_run,
    model_summary,
    objective_id,
    optional_business_output,
    remove_exact_duplicates,
    split_metadata,
    target_column,
    train_models,
    validate_inputs,
)


def _configuration_for_run(
    configuration: dict[str, Any], profile: dict[str, Any], warnings: list[str],
) -> dict[str, Any]:
    """Use the actual configuration algorithm while preserving valid caller intent."""

    requested = build_configuration(
        dataset_identifier(configuration), objective_id(configuration), target_column(configuration), profile,
    )
    if requested.get("valid") and requested.get("problem_type") in {"classification", "regression", "clustering"}:
        return requested
    warnings.append("Fresh configuration validation was unavailable; the supplied valid experiment configuration was used.")
    return dict(configuration)


def _workflow_module_metadata(workflow: dict[str, Any], pruned: dict[str, Any], execution: dict[str, Any], trained: bool) -> tuple[list[str], list[str], list[str]]:
    selected = [node["id"] for node in workflow.get("nodes", []) if node.get("id") not in CORE_WORKFLOW_NODES]
    pruned_ids = [item["node_id"] for item in pruned.get("pruned_nodes", []) if item.get("node_id") not in CORE_WORKFLOW_NODES]
    executed = [
        item["node_id"] for item in execution.get("node_results", [])
        if item.get("status") == "completed" and item.get("node_id") not in CORE_WORKFLOW_NODES
    ]
    task = next((node_id for node_id in ("classification", "regression", "clustering") if node_id in selected), None)
    # Phase 5 rightfully skips model nodes; the fresh Phase 6 call below is
    # the real execution of that selected workflow task, so count it once.
    if trained and task and task not in executed:
        executed.append(task)
    return selected, pruned_ids, executed


def run_awof_pipeline(
    dataframe: pd.DataFrame,
    configuration: dict[str, Any],
    profile: dict[str, Any] | None,
    random_state: int = 42,
    experiment_name: str | None = None,
) -> dict[str, Any]:
    """Run the actual adaptive AWOF stages once and return a JSON-safe record."""

    validate_inputs(dataframe, configuration)
    effective_state, state_warnings = effective_random_state(random_state)

    def operation() -> dict[str, Any]:
        overall_started = perf_counter()
        warnings = list(state_warnings)
        dataset_id = dataset_identifier(configuration)

        profiling_started = perf_counter()
        fresh_profile = DatasetProfiler(dataframe.copy(deep=True), dataset_id).generate_profile()
        profiling_ms = round((perf_counter() - profiling_started) * 1_000, 3)

        design_started = perf_counter()
        effective_configuration = _configuration_for_run(configuration, fresh_profile, warnings)
        acsa = ACSAScorer(fresh_profile, effective_configuration, dataframe.copy(deep=True)).generate()
        awga = AWGAGenerator(fresh_profile, effective_configuration, acsa).generate()
        design_ms = round((perf_counter() - design_started) * 1_000, 3)

        pruning_started = perf_counter()
        target = target_column(effective_configuration)
        pruned = prune(awga, dataframe.copy(deep=True), target, effective_configuration["problem_type"])
        pruning_ms = round((perf_counter() - pruning_started) * 1_000, 3)

        execution_started = perf_counter()
        execution = execute(
            pruned,
            dataframe.copy(deep=True),
            dataset_id,
            target,
            effective_configuration["problem_type"],
            objective_id(effective_configuration),
        )
        execution_ms = round((perf_counter() - execution_started) * 1_000, 3)
        if execution.get("errors"):
            warnings.extend(f"Workflow execution warning: {message}" for message in execution["errors"])

        recommendation_started = perf_counter()
        amra = AMRARecommender().recommend(fresh_profile, effective_configuration, execution, dataframe.copy(deep=True))
        recommendation_ms = round((perf_counter() - recommendation_started) * 1_000, 3)

        prep_started = perf_counter()
        comparable_dataframe, duplicate_info = remove_exact_duplicates(dataframe)
        preprocessing_ms = round((perf_counter() - prep_started) * 1_000, 3)
        evaluation, pipelines, training_timings = train_models(
            comparable_dataframe, effective_configuration, amra, fresh_profile,
        )
        model_info = model_summary(amra, evaluation, pipelines, effective_configuration["problem_type"])
        selected_ids, pruned_ids, executed_ids = _workflow_module_metadata(
            awga, pruned, execution, bool(model_info["trained"]),
        )
        business_output = optional_business_output(
            comparable_dataframe, effective_configuration, fresh_profile, pipelines, evaluation,
        )
        # Phase 7 output is generated directly from the fresh fitted best
        # pipeline, outside the older Phase 5 executor's placeholder nodes.
        # Count those logical workflow modules only when they were selected,
        # survived pruning, and actually produced compact output.
        retained_ids = set(selected_ids) - set(pruned_ids)
        if business_output.get("status") == "completed":
            if "explainability" in retained_ids and "explainability" not in executed_ids:
                executed_ids.append("explainability")
            if business_output.get("cips") is not None and "business_prioritization" in retained_ids and "business_prioritization" not in executed_ids:
                executed_ids.append("business_prioritization")
        if business_output.get("warnings"):
            warnings.extend(str(item) for item in business_output["warnings"])
        timings = {
            "profiling": profiling_ms,
            "configuration_acsa_awga": design_ms,
            "preprocessing": preprocessing_ms,
            "pruning": pruning_ms,
            "execution": execution_ms,
            "model_recommendation": recommendation_ms,
            **training_timings,
            "overall": round((perf_counter() - overall_started) * 1_000, 3),
        }
        warnings.append(
            "Primary predictive metrics use a fresh Phase 6 split/fitted pipeline; full-frame Phase 5 execution is measured separately and is not used for evaluation."
        )
        result = base_result(
            pipeline_name="awof_adaptive",
            configuration=effective_configuration,
            random_state=effective_state,
            split=split_metadata(comparable_dataframe, effective_configuration, effective_state),
            module_ids=executed_ids,
            pruned_module_ids=pruned_ids,
            model_info=model_info,
            timings=timings,
            warnings=warnings,
            experiment_name=experiment_name,
        )
        result.update({
            "acsa": acsa,
            "awga": awga,
            "pruning": pruned,
            "execution": execution,
            "amra": amra,
            "business_output": business_output,
            "preparation": duplicate_info,
            "acsa_decisions": acsa.get("summary", {}),
            "awga_node_count": len(awga.get("nodes", [])),
            "pruned_modules": len(pruned_ids),
            "executed_modules": len(executed_ids),
            "amra_candidates": model_info["considered"],
            "amra_selected_models": model_info["selected"],
            "trained_models": model_info["trained"],
            "workflow_modules": {
                "considered": len(selected_ids),
                "executed": len(executed_ids),
                "selected": len(selected_ids),
                "pruned": len(pruned_ids),
                "ids": executed_ids,
                "selected_ids": selected_ids,
                "pruned_ids": pruned_ids,
            },
        })
        return json_safe(result)

    result, resources = measure_entire_run(operation)
    return attach_resources(result, resources)
