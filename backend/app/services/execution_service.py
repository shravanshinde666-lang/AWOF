"""Workflow execution and reproducible-notebook services."""

import json

from awof.execution.executor import execute
from awof.pruning import prune

from ..database import repository
from .configuration_service import get_saved_configuration
from .dataset_service import load_dataset_dataframe
from .workflow_service import get_workflow


def prune_workflow(dataset_id):
    configuration = get_saved_configuration(dataset_id)
    pruned = prune(get_workflow(dataset_id), load_dataset_dataframe(dataset_id),
                   (configuration.get("target") or {}).get("column"), configuration["problem_type"])
    repository.save_stage(dataset_id, "pruned_workflow", pruned)
    return pruned


def get_pruned(dataset_id):
    try:
        return repository.get_stage(dataset_id, "pruned_workflow")
    except repository.PersistenceNotFoundError as exc:
        raise KeyError("Workflow has not been pruned.") from exc


def execute_workflow(dataset_id):
    configuration = get_saved_configuration(dataset_id)
    result = execute(get_pruned(dataset_id), load_dataset_dataframe(dataset_id), dataset_id,
                     (configuration.get("target") or {}).get("column"), configuration["problem_type"],
                     configuration["business_objective"]["id"])
    repository.save_stage(dataset_id, "execution", result)
    return result


def get_execution(dataset_id):
    try:
        return repository.get_stage(dataset_id, "execution")
    except repository.PersistenceNotFoundError as exc:
        raise KeyError("Workflow has not been executed.") from exc


def _markdown_cell(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.splitlines()]}


def _code_cell(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [line + "\n" for line in source.splitlines()]}


def _replay_source(step, details):
    """Create a safe replay cell from the exact recorded method metadata."""
    if step == "duplicate_handling":
        return "working_df = working_df.drop_duplicates().copy()\nprint('Rows after duplicate removal:', len(working_df))"
    if step == "missing_values":
        strategies = repr(details.get("strategy_per_column", {}))
        return f'''strategies = {strategies}
for column, strategy in strategies.items():
    if strategy == "median":
        working_df[column] = working_df[column].fillna(working_df[column].median())
    else:
        mode = working_df[column].mode(dropna=True)
        working_df[column] = working_df[column].fillna(mode.iloc[0] if not mode.empty else "Unknown")
print("Imputed columns:", list(strategies))'''
    if step == "encoding":
        columns = repr(details.get("columns_encoded", []))
        return f'''encoding_columns = {columns}
available_columns = [column for column in encoding_columns if column in working_df]
working_df = pd.get_dummies(working_df, columns=available_columns, dtype=float)
print("Encoded columns:", available_columns)
print("Feature count after encoding:", working_df.shape[1] - (TARGET_COLUMN in working_df.columns))'''
    if step == "scaling":
        columns = repr(details.get("columns_scaled", []))
        return f'''from sklearn.preprocessing import StandardScaler

scale_columns = [column for column in {columns} if column in working_df]
if scale_columns:
    working_df[scale_columns] = StandardScaler().fit_transform(working_df[scale_columns])
print("Scaled columns:", scale_columns)'''
    if step == "outlier_analysis":
        return "# AWOF flags IQR outliers for review; it does not automatically remove rows.\nprint('Outliers were flagged; working data remains unchanged.')"
    if step == "feature_selection":
        removed = repr(details.get("removed_features", []))
        return f'''removed_features = {removed}
working_df = working_df.drop(columns=[column for column in removed_features if column in working_df], errors="ignore")
print("Removed features:", removed_features)'''
    if step == "dimensionality_reduction":
        components = repr(details.get("components") or 0.95)
        return f'''# Refit PCA only on training folds to avoid leakage during modelling.
from sklearn.decomposition import PCA

pca_columns = [column for column in working_df.select_dtypes(include=np.number) if column != TARGET_COLUMN]
if len(pca_columns) >= 2:
    pca = PCA(n_components={components})
    values = pca.fit_transform(working_df[pca_columns])
    working_df = working_df.drop(columns=pca_columns).join(pd.DataFrame(values, index=working_df.index).add_prefix("pca_"))
    print("PCA components:", values.shape[1])
else:
    print("Not applicable: PCA requires at least two numerical features.")'''
    if step == "temporal_analysis":
        return "# Temporal features were prepared by AWOF; see the audit below for generated names."
    if step == "text_analysis":
        return "# Text preparation is deferred to the estimator-specific training pipeline."
    return "# This stage is documented in the execution audit and handled by its dedicated AWOF module."


def build_execution_notebook(dataset_id):
    """Build a privacy-preserving, executable EDA and preprocessing notebook."""
    execution = get_execution(dataset_id)
    configuration = get_saved_configuration(dataset_id)
    target = (configuration.get("target") or {}).get("column")
    completed = [item for item in execution.get("node_results", []) if item.get("status") == "completed"]
    audit = [{"step": item["node_id"], "duration_ms": item["duration_ms"],
              "rows_before": item["rows_before"], "rows_after": item["rows_after"],
              "columns_before": item["columns_before"], "columns_after": item["columns_after"],
              "details": item.get("details", {})} for item in completed]
    cells = [
        _markdown_cell("# AWOF reproducible EDA and preprocessing notebook\n\nThis generated notebook contains executable exploratory analysis and a replay of the completed AWOF preprocessing steps. Uploaded rows are never embedded: set `DATA_PATH` to a local copy of the original file."),
        _code_cell(f'''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = "your_uploaded_dataset.csv"  # Change this path
TARGET_COLUMN = {target!r}
path = Path(DATA_PATH)
df = pd.read_excel(path) if path.suffix.lower() in {{".xlsx", ".xls"}} else pd.read_csv(path)
working_df = df.copy(deep=True)
print(f"Loaded {{working_df.shape[0]:,}} rows and {{working_df.shape[1]:,}} columns")
print("Target column:", TARGET_COLUMN or "None selected")'''),
        _markdown_cell("## 1. Dataset overview"),
        _code_cell('''display(working_df.head())
display(working_df.describe(include="all").T)
print("Shape:", working_df.shape)
print("Memory usage (MB):", round(working_df.memory_usage(deep=True).sum() / 1024**2, 3))
working_df.info()'''),
        _markdown_cell("## 2. Data-quality analysis"),
        _code_cell('''missing = working_df.isna().sum().sort_values(ascending=False)
quality = pd.DataFrame({"missing_count": missing, "missing_pct": (missing / len(working_df) * 100).round(3), "unique_values": working_df.nunique(dropna=True)})
display(quality)
print("Duplicate rows:", int(working_df.duplicated().sum()))
print("Constant columns:", quality.index[quality["unique_values"] <= 1].tolist())
if missing.gt(0).any():
    missing[missing.gt(0)].plot(kind="bar", figsize=(10, 4), color="#4de4c1", title="Missing values by column")
    plt.ylabel("Count"); plt.tight_layout(); plt.show()
else:
    print("No missing values detected.")'''),
        _markdown_cell("## 3. Numerical exploratory data analysis"),
        _code_cell('''numeric_columns = working_df.select_dtypes(include=np.number).columns.tolist()
if numeric_columns:
    display(working_df[numeric_columns].describe().T)
    working_df[numeric_columns].hist(figsize=(14, max(3, len(numeric_columns) * 2)), bins=30, edgecolor="white")
    plt.suptitle("Numerical feature distributions"); plt.tight_layout(); plt.show()
    working_df[numeric_columns].boxplot(figsize=(max(8, len(numeric_columns) * 1.2), 4), rot=45)
    plt.title("Numerical feature boxplots"); plt.tight_layout(); plt.show()
else:
    print("Not applicable: no numerical columns were detected.")'''),
        _markdown_cell("## 4. Categorical exploratory data analysis"),
        _code_cell('''categorical_columns = working_df.select_dtypes(exclude=np.number).columns.tolist()
for column in categorical_columns[:8]:
    counts = working_df[column].astype("string").fillna("Missing").value_counts().head(12)
    display(pd.DataFrame({column: counts.index, "count": counts.values}))
    counts.sort_values().plot(kind="barh", figsize=(8, max(3, len(counts) * 0.35)), color="#b9ff2d", title=f"Top values: {column}")
    plt.tight_layout(); plt.show()
if not categorical_columns:
    print("Not applicable: no categorical columns were detected.")'''),
        _markdown_cell("## 5. Correlation and outlier review"),
        _code_cell('''if len(numeric_columns) >= 2:
    correlation = working_df[numeric_columns].corr(numeric_only=True)
    display(correlation.round(3))
    plt.figure(figsize=(max(7, len(numeric_columns)), max(5, len(numeric_columns) * 0.75)))
    plt.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xticks(range(len(numeric_columns)), numeric_columns, rotation=45, ha="right")
    plt.yticks(range(len(numeric_columns)), numeric_columns); plt.colorbar(label="Pearson correlation")
    plt.title("Correlation heatmap"); plt.tight_layout(); plt.show()
    outliers = []
    for column in numeric_columns:
        q1, q3 = working_df[column].quantile([0.25, 0.75]); iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((working_df[column] < lower) | (working_df[column] > upper)).sum())
        outliers.append([column, count, round(count / len(working_df) * 100, 3), lower, upper])
    display(pd.DataFrame(outliers, columns=["column", "outlier_count", "outlier_pct", "lower_bound", "upper_bound"]))
else:
    print("Not applicable: correlation requires at least two numerical columns.")'''),
    ]
    for item in audit:
        if item["step"] in {"dataset_input", "profile", "output"}:
            continue
        cells.extend([_markdown_cell(f"## Applied AWOF method: {item['step'].replace('_', ' ').title()}\n\nRecorded effect: {item['rows_before']} -> {item['rows_after']} rows; {item['columns_before']} -> {item['columns_after']} columns; duration {item['duration_ms']} ms."), _code_cell(_replay_source(item["step"], item["details"]))])
    cells.extend([_markdown_cell("## AWOF execution audit"), _code_cell("applied_steps = " + json.dumps(audit, indent=2) + "\nfor step in applied_steps:\n    print(f\"{step['step']}: {step['rows_before']} -> {step['rows_after']} rows, {step['columns_before']} -> {step['columns_after']} columns\")")])
    return json.dumps({"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}, "awof": {"dataset_id": dataset_id, "workflow_id": execution.get("workflow_id"), "summary": execution.get("summary", {}), "target_column": target}}, "nbformat": 4, "nbformat_minor": 5}, indent=2)
