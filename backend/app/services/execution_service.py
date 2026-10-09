import json

from awof.pruning import prune
from awof.execution.executor import execute
from .workflow_service import get_workflow
from .dataset_service import load_dataset_dataframe
from .configuration_service import get_saved_configuration
from ..database import repository
def prune_workflow(dataset_id):
 c=get_saved_configuration(dataset_id);p=prune(get_workflow(dataset_id),load_dataset_dataframe(dataset_id),(c.get("target")or{}).get("column"),c["problem_type"]);repository.save_stage(dataset_id,"pruned_workflow",p);return p
def get_pruned(dataset_id):
 try:return repository.get_stage(dataset_id,"pruned_workflow")
 except repository.PersistenceNotFoundError as exc:raise KeyError("Workflow has not been pruned.") from exc
def execute_workflow(dataset_id):
 c=get_saved_configuration(dataset_id);p=get_pruned(dataset_id);r=execute(p,load_dataset_dataframe(dataset_id),dataset_id,(c.get("target")or{}).get("column"),c["problem_type"],c["business_objective"]["id"]);repository.save_stage(dataset_id,"execution",r);return r
def get_execution(dataset_id):
 try:return repository.get_stage(dataset_id,"execution")
 except repository.PersistenceNotFoundError as exc:raise KeyError("Workflow has not been executed.") from exc

def build_execution_notebook(dataset_id):
 execution=get_execution(dataset_id)
 completed=[item for item in execution.get("node_results",[]) if item.get("status")=="completed"]
 audit=[{"step":item["node_id"],"duration_ms":item["duration_ms"],"rows_before":item["rows_before"],"rows_after":item["rows_after"],"columns_before":item["columns_before"],"columns_after":item["columns_after"],"details":item.get("details",{})} for item in completed]
 def markdown_cell(text):return {"cell_type":"markdown","metadata":{},"source":[line+"\n" for line in text.splitlines()]}
 def code_cell(source):return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":[line+"\n" for line in source.splitlines()]}
 cells=[markdown_cell("# AWOF reproducible EDA and preprocessing notebook\n\nThis generated notebook contains executable exploratory data analysis and the preprocessing operations recorded by AWOF. It does not embed uploaded data; set `DATA_PATH` to a local copy of the original file."),code_cell('''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = "your_uploaded_dataset.csv"  # Change this path
path = Path(DATA_PATH)
if path.suffix.lower() in {".xlsx", ".xls"}:
    df = pd.read_excel(path)
else:
    df = pd.read_csv(path)
working_df = df.copy(deep=True)
print(f"Loaded {working_df.shape[0]:,} rows and {working_df.shape[1]:,} columns")'''),markdown_cell("## 1. Dataset overview"),code_cell('''display(working_df.head())
display(working_df.describe(include="all").T)
print("Shape:", working_df.shape)
print("Memory usage (MB):", round(working_df.memory_usage(deep=True).sum() / 1024**2, 3))
working_df.info()'''),markdown_cell("## 2. Data-quality analysis"),code_cell('''missing = working_df.isna().sum().sort_values(ascending=False)
quality = pd.DataFrame({"missing_count": missing, "missing_pct": (missing / len(working_df) * 100).round(3), "unique_values": working_df.nunique(dropna=True)})
display(quality)
print("Duplicate rows:", int(working_df.duplicated().sum()))
print("Constant columns:", quality.index[quality["unique_values"] <= 1].tolist())

if missing.gt(0).any():
    plt.figure(figsize=(10, 4))
    missing[missing.gt(0)].plot(kind="bar", color="#4de4c1")
    plt.title("Missing values by column"); plt.ylabel("Count"); plt.tight_layout(); plt.show()'''),markdown_cell("## 3. Numerical exploratory data analysis"),code_cell('''numeric_columns = working_df.select_dtypes(include=np.number).columns.tolist()
if numeric_columns:
    display(working_df[numeric_columns].describe().T)
    working_df[numeric_columns].hist(figsize=(14, max(3, len(numeric_columns) * 2)), bins=30, edgecolor="white")
    plt.suptitle("Numerical feature distributions"); plt.tight_layout(); plt.show()
    plt.figure(figsize=(max(8, len(numeric_columns) * 1.2), 4))
    working_df[numeric_columns].boxplot(rot=45)
    plt.title("Numerical feature boxplots"); plt.tight_layout(); plt.show()
else:
    print("Not applicable: no numerical columns were detected.")'''),markdown_cell("## 4. Categorical exploratory data analysis"),code_cell('''categorical_columns = working_df.select_dtypes(exclude=np.number).columns.tolist()
for column in categorical_columns[:8]:
    counts = working_df[column].astype("string").fillna("Missing").value_counts().head(12)
    display(pd.DataFrame({column: counts.index, "count": counts.values}))
    counts.sort_values().plot(kind="barh", figsize=(8, max(3, len(counts) * .35)), color="#b9ff2d", title=f"Top values: {column}")
    plt.tight_layout(); plt.show()
if not categorical_columns:
    print("Not applicable: no categorical columns were detected.")'''),markdown_cell("## 5. Correlation and outlier review"),code_cell('''if len(numeric_columns) >= 2:
    correlation = working_df[numeric_columns].corr(numeric_only=True)
    display(correlation.round(3))
    plt.figure(figsize=(max(7, len(numeric_columns)), max(5, len(numeric_columns) * .75)))
    plt.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xticks(range(len(numeric_columns)), numeric_columns, rotation=45, ha="right")
    plt.yticks(range(len(numeric_columns)), numeric_columns); plt.colorbar(label="Pearson correlation")
    plt.title("Correlation heatmap"); plt.tight_layout(); plt.show()

    outlier_summary = []
    for column in numeric_columns:
        q1, q3 = working_df[column].quantile([.25, .75]); iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((working_df[column] < lower) | (working_df[column] > upper)).sum())
        outlier_summary.append([column, count, round(count / len(working_df) * 100, 3), lower, upper])
    display(pd.DataFrame(outlier_summary, columns=["column", "outlier_count", "outlier_pct", "lower_bound", "upper_bound"]))
else:
    print("Not applicable: correlation requires at least two numerical columns.")''')]
 for item in audit:
  step=item["step"]
  if step in {"dataset_input","profile","output"}:continue
  cells.append(markdown_cell(f"## Applied AWOF method: {step.replace('_',' ').title()}\n\nRecorded effect: {item['rows_before']}→{item['rows_after']} rows; {item['columns_before']}→{item['columns_after']} columns; duration {item['duration_ms']} ms."))
  source={"duplicate_handling":"working_df = working_df.drop_duplicates().copy()\nprint('Rows after duplicate removal:', len(working_df))","missing_values":"for column in working_df.columns:\n    if working_df[column].isna().any():\n        if pd.api.types.is_numeric_dtype(working_df[column]):\n            working_df[column] = working_df[column].fillna(working_df[column].median())\n        else:\n            mode = working_df[column].mode(dropna=True)\n            working_df[column] = working_df[column].fillna(mode.iloc[0] if not mode.empty else 'Unknown')","encoding":"categorical_columns = working_df.select_dtypes(exclude=np.number).columns.tolist()\nworking_df = pd.get_dummies(working_df, columns=categorical_columns, dtype=float)\nprint('Encoded feature count:', working_df.shape[1])","scaling":"from sklearn.preprocessing import StandardScaler\nscale_columns = [c for c in working_df.select_dtypes(include=np.number).columns if working_df[c].nunique() > 2]\nworking_df[scale_columns] = StandardScaler().fit_transform(working_df[scale_columns])","outlier_analysis":"# AWOF records IQR outliers for review; no rows are automatically removed.\nprint('Outliers were flagged for inspection; working data remains unchanged.')","feature_selection":"# Feature selection was evaluated by AWOF. Review the workflow audit and training pipeline for the selected estimator-specific features.","dimensionality_reduction":"# Dimensionality reduction was evaluated by AWOF. Reproduce PCA only after selecting feature columns and fitting on training data."}.get(step,"# This stage is documented in the execution audit; it is handled by its dedicated AWOF module.")
  cells.append(code_cell(source))
 cells.extend([markdown_cell("## AWOF execution audit"),code_cell("applied_steps = "+json.dumps(audit,indent=2)+"\nfor step in applied_steps:\n    print(f\"{step['step']}: {step['rows_before']}→{step['rows_after']} rows, {step['columns_before']}→{step['columns_after']} columns\")")])
 notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3"},"awof":{"dataset_id":dataset_id,"workflow_id":execution.get("workflow_id"),"summary":execution.get("summary",{})}},"nbformat":4,"nbformat_minor":5}
 return json.dumps(notebook,indent=2)
