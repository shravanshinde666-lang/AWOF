# AWOF Complete Project Guide

## 1. Project identity

**Project name:** AWOF - Adaptive Workflow Optimization Framework

**Project type:** Full-stack, dataset-aware machine-learning workflow system

**Primary purpose:** Convert an uploaded tabular dataset into a profiled, configured,
optimized, trained, evaluated, explained, and business-prioritized analytics project.

AWOF is designed to avoid applying the same fixed pipeline to every dataset. It first
inspects the real data, records a user-approved objective and target, calculates which
capabilities are appropriate, builds an adaptive workflow, removes unnecessary steps,
and then runs the useful parts of the pipeline.

The framework supports:

- binary and multiclass classification;
- numeric regression;
- unsupervised clustering/segmentation;
- CSV, XLSX, and legacy XLS datasets;
- local SQLite development and PostgreSQL production persistence;
- browser-based dashboards, reports, charts, and workflow inspection.

## 2. Main problem solved by AWOF

Traditional ML examples often use a fixed sequence such as:

```text
Clean -> Encode -> Scale -> Train every model -> Select one
```

That sequence may run unnecessary operations, mishandle identifiers, leak information
from test data, or use models that do not suit the dataset. AWOF instead uses:

```text
Understand data -> Understand objective -> Select capabilities -> Build workflow
-> Prune unnecessary work -> Execute preparation -> Recommend models
-> Train safely -> Evaluate -> Explain -> Prioritize -> Compare
```

The important distinction is that AWOF stores the evidence behind its decisions.
Users can inspect why a capability ran, why a workflow node was pruned, why a model
was recommended, and which measured metric selected the best model.

## 3. Complete end-to-end pipeline

```text
1. Dataset Upload
       |
2. Dataset Intelligence / Profiling
       |
3. Objective and Target Configuration
       |
4. ACSA Capability Decisions
       |
5. AWGA Workflow Generation
       |
6. Workflow Pruning
       |
7. Workflow Execution
       |
8. AMRA Model Recommendation
       |
9. Leakage-Safe Training and Evaluation
       |
10. Model Explainability
       |
11. CIPS Business Prioritization
       |
12. Fixed Pipeline vs AWOF Research Comparison
       |
13. Final Printable Report
```

Each stage uses the persisted output of earlier stages. A later stage does not invent
information that is missing from the dataset or configuration.

## 4. Stage-by-stage implementation

### 4.1 Dataset upload and ingestion

**What is implemented**

- Upload support for `.csv`, `.xlsx`, and `.xls`.
- Maximum upload size is configurable and defaults to 50 MB.
- Filenames are sanitized before storage.
- The uploaded file is assigned a UUID dataset/project identifier.
- Metadata, dimensions, column names, status, and timestamps are persisted.
- A preview endpoint returns bounded rows instead of exposing the complete file.
- Dataset deletion removes the associated safe project artifacts.

**What this stage produces**

- a stored source file in `storage/uploads/`;
- dataset metadata in the database;
- a dataset ID used by every later API and page;
- a small preview for user validation.

**Why it matters**

CSV and Excel parsing do not behave identically. AWOF normalizes ingestion so both
formats enter the same profiling and analysis pipeline.

### 4.2 Dataset Intelligence Engine

Dataset Intelligence is descriptive. It examines the data without modifying the
uploaded source.

**Implemented profile information**

- row count, column count, and memory usage;
- missing cells, missing percentages, and affected columns;
- duplicate row count and percentage;
- per-column cardinality and detected broad/detailed type;
- identifier-candidate and constant-column signals;
- numeric-like string detection and safe conversion for analysis;
- numeric statistics: count, mean, median, mode, min, max, range, variance,
  standard deviation, quartiles, IQR, and skewness;
- categorical statistics: unique count, mode, frequency, mode percentage, and
  bounded top values;
- IQR-based outlier counts and bounds;
- bounded numerical histogram data;
- Pearson correlation pairs and a correlation matrix where valid;
- target distribution after configuration;
- target rate by useful categorical features for classification;
- data-quality summary and quality indicators.

Whitespace-only cells are treated as missing values. A numeric-like column such as
Telco `TotalCharges` is analyzed numerically while its blank values remain recorded as
missing. Identifier candidates such as `customerID` are shown in the profile but are
excluded from misleading charts, correlations, and model features.

**Visual output**

- dataset KPI and quality cards;
- target distribution;
- useful numeric distributions;
- categorical distributions;
- missing-values visualization;
- top correlations and heatmap when meaningful;
- classification target-rate-by-category charts;
- tabbed tables for columns, statistics, outliers, and correlations.

**What this stage does not do**

It does not impute, delete, encode, scale, or train. It describes the source data so
the following algorithms can make traceable decisions.

### 4.3 Analysis configuration

The user selects a business objective and approves the target when one is required.

| Objective | Typical target requirement | Likely problem type |
| --- | --- | --- |
| Predict Behavior | Required | Classification or regression |
| Identify Risk | Required | Classification or regression |
| Analyze Retention | Required | Classification |
| Segment Customers | No target | Clustering |
| Optimize Revenue | Optional | Regression or business analysis |

Target suggestions use real profile signals. Identifiers, constants, and all-null
columns are unsuitable. Binary/categorical targets suggest classification, while
usable continuous numeric targets suggest regression. Suggestions assist the user;
they do not replace domain approval.

### 4.4 ACSA - Adaptive Capability Scoring Algorithm

ACSA converts the corrected profile and saved configuration into capability decisions.
Every capability contains a normalized score, decision, reasons, and input signals.

| Score | Decision | Meaning |
| --- | --- | --- |
| `0.70-1.00` | RUN | Capability is strongly applicable |
| `0.40-0.69` | OPTIONAL | Useful only when supporting conditions justify it |
| `< 0.40` | SKIP | Capability is not supported by current evidence |

Capabilities cover missing values, duplicates, outliers, encoding, scaling, feature
selection, dimensionality reduction, text/temporal analysis, classification,
regression, clustering, imbalance handling, explainability, and business priority.

Examples of actual signals used include overall and maximum column missingness,
duplicate percentage, categorical/numeric feature share, IQR outliers, feature width,
identifiers, constants, high cardinality, correlations, objective, problem type, and
class balance. Results are not hardcoded for the Telco dataset.

The UI presents RUN/OPTIONAL/SKIP KPI cards, a decision distribution, a sorted score
chart, grouped capability cards, and expandable reasons/signals.

### 4.5 AWGA - Adaptive Workflow Generation Algorithm

AWGA turns ACSA decisions into a directed acyclic graph (DAG).

It creates core input/profile/output nodes, adds justified capabilities, calculates
dependencies, validates that there are no cycles, and returns a deterministic
topological execution order. RUN capabilities are included. OPTIONAL capabilities are
included only when supporting rules justify them. SKIP capabilities remain visible as
excluded evidence rather than silently disappearing.

The React Flow interface provides:

- automatic readable layout;
- visible directed edges and arrows;
- status colors and legend;
- workflow summary KPIs;
- selectable node detail panel;
- execution order;
- original versus optimized workflow summary;
- readable pruning/exclusion evidence.

### 4.6 Workflow pruning

Pruning rechecks the generated plan against the working dataset immediately before
execution. A node can be removed when its execution condition is absent, for example:

- no duplicates to handle;
- no missing values to prepare;
- no categorical columns to encode;
- no meaningful scaling requirement;
- insufficient numeric width for PCA;
- no feature-filtering evidence.

When a node is pruned, predecessor and successor edges are safely reconnected. The
optimized graph remains ordered and connected. Each decision stores its reason and
signals as pruning evidence.

### 4.7 Workflow execution

Execution uses an immutable source DataFrame and a separate working copy. Supported
modules include duplicate handling, missing-value preparation, categorical encoding,
scaling, IQR outlier analysis, feature filtering/selection, PCA preparation, temporal
preparation, and text preparation.

The execution timeline records:

- node name and final status;
- human-readable duration;
- rows and columns before and after;
- transformation details;
- warnings and safe failure information;
- completed, pruned, deferred, skipped, and failed counts.

Status semantics are important:

| Status | Meaning |
| --- | --- |
| `COMPLETED` | This stage actually executed successfully |
| `PRUNED` | Removed because live data showed it was unnecessary |
| `SKIPPED` | Intentionally not applicable or excluded |
| `DEFERRED` | Preserved for its dedicated later stage |
| `FAILED` | Attempted but did not complete |

ML training, explainability, and business-priority nodes are marked `DEFERRED` during
preprocessing execution. They are not incorrectly presented as ordinary skipped work.

### 4.8 AMRA - Adaptive Model Recommendation Algorithm

AMRA ranks compatible models before training. Its suitability score is a heuristic
based on real profile, configuration, execution, data-size, feature-type, balance,
correlation, dimensionality, and scaling signals. It is not a performance metric.

| Problem | Implemented model families |
| --- | --- |
| Classification | Logistic Regression, Random Forest, Gradient Boosting, optional XGBoost |
| Regression | Linear Regression, Ridge, Random Forest, Gradient Boosting, optional XGBoost |
| Clustering | K-Means, DBSCAN, Agglomerative Clustering |

Up to three supervised models or two clustering models are recommended. XGBoost is
reported as unavailable when its optional package is not installed; AWOF does not
silently substitute a different estimator.

Training is exposed as a polled job so the UI can show model-by-model progress instead
of appearing frozen during slower training.

### 4.9 Leakage-safe training and evaluation

Supervised evaluation starts from selected raw features, drops missing target rows,
and removes the target, identifiers, and constants. It then performs a deterministic
80/20 train/test split using random state 42. Classification is stratified when the
class counts permit it.

All learned preprocessing is fitted inside a scikit-learn pipeline on training data:

- numerical: median imputation and model-dependent scaling;
- categorical: most-frequent imputation and one-hot encoding with unknown-category
  handling;
- estimator: the AMRA-recommended model.

Cross-validation clones the complete pipeline for each fold. This prevents information
from the test set or validation fold from leaking into imputation, encoding, scaling,
or the estimator.

**Evaluation metrics**

| Problem | Metrics |
| --- | --- |
| Classification | Accuracy, weighted precision, weighted recall, weighted F1, ROC-AUC when valid, confusion matrix |
| Regression | MAE, MSE, RMSE, R-squared, MAPE when valid |
| Clustering | Silhouette, Davies-Bouldin, Calinski-Harabasz, cluster count, DBSCAN noise information |

Best-model selection uses held-out results: highest F1 then ROC-AUC for classification,
lowest RMSE for regression, and highest valid silhouette for clustering. Only the
selected best complete pipeline is stored in `storage/models/` using Joblib.

Matplotlib runs in a non-interactive backend to generate durable PNG model-comparison
and classification confusion-matrix charts from actual evaluation results.

### 4.10 Explainability

The explainability engine loads the saved best pipeline; it does not retrain the model.
It preserves transformed feature names from the fitted `ColumnTransformer` and
provides global importance plus a bounded local row explanation.

Actual method labels are preserved:

- tree models: `native_feature_importance` globally and
  `native_importance_proxy` locally;
- linear models: `linear_coefficients`;
- other supported estimators: `permutation_importance` where a target is available;
- SHAP: only when the optional dependency is installed and compatible.

Native tree importance is not a signed contribution. The UI therefore displays it as
importance/local importance proxy and does not claim that it increased or decreased
the prediction. Signed positive/negative presentation is used only when the selected
method genuinely supplies direction. Limitations and fallback warnings are shown.

### 4.11 CIPS - Customer Intervention Priority Score

CIPS answers a different question from prediction and explanation:

```text
Prediction:     What is likely to happen?
Explanation:    Why did the model produce this output?
CIPS:           Which applicable entities should be reviewed first?
```

CIPS combines a usable supervised prediction signal with conservatively detected
business variables. Potential signals are risk, business value, engagement,
complaint/support activity, sentiment, and recency. Only real detected signals are
used, and their weights are renormalized.

```text
CIPS = 100 * sum(effective_weight_i * normalized_signal_i)
```

Base weights are risk 0.45, business value 0.25, engagement 0.10, complaint/support
0.10, sentiment 0.05, and recency 0.05. Scores are bounded to 0-100.

| CIPS score | Priority |
| --- | --- |
| `85-100` | Immediate |
| `70-<85` | High |
| `40-<70` | Medium |
| `0-<40` | Monitor |

The UI includes four priority KPI cards, priority distribution, score distribution,
risk-versus-value scatter when both signals exist, top entity details, a searchable,
filterable, sortable and paginated table, calculation details, and CSV export. A map is
not shown unless genuine geographic fields exist. Clustering correctly returns CIPS as
not applicable.

### 4.12 Research comparison

The research stage compares a deterministic fixed tabular pipeline with the actual
adaptive AWOF path using the same source data, target, split policy, and random state.

It measures:

- named workflow modules;
- number of models trained;
- wall-clock runtime;
- Python-tracked peak allocation memory;
- problem-appropriate primary metric: F1, RMSE, or silhouette;
- full supporting model metrics;
- repeated-run mean and standard deviation.

The UI visualizes Fixed versus AWOF results for modules, models, runtime, memory, and
the primary metric. Interpretation is factual and dataset-specific; the application
does not claim statistical superiority from a small experiment.

Artifacts are stored under `experiments/results/` as metrics, Markdown reports, CSV
summaries, and charts.

### 4.13 Overview and final report

The Overview dashboard reads actual persisted stage results. It shows dataset health,
target/problem type, stage completion, ACSA decisions, best model, explanation method,
CIPS summary, and research availability. Missing stages receive graceful empty states.

The final report uses existing results without rerunning algorithms. Its order is:

```text
Dataset -> Profile -> Configuration -> ACSA -> AWGA -> Execution -> AMRA
-> Evaluation -> Explainability -> CIPS -> Research -> Limitations
```

The report provides a browser Print / Save PDF action and print-friendly styling.

## 5. Practical use cases

### Use case A: Customer churn prediction

Example data: customer ID, contract, tenure, monthly charges, support activity, and a
`Churn` Yes/No target.

AWOF can identify the binary target, keep the customer ID only as an entity identifier,
detect blanks in numeric-like charges, calculate class balance, recommend classifiers,
evaluate the held-out F1/ROC-AUC, explain the best model, and rank customers with CIPS
when risk and business signals are available.

### Use case B: Fraud or default risk

Example target: fraud/no-fraud or default/no-default. ACSA can recognize classification
and imbalance-handling relevance. AMRA can favor models appropriate for non-linear or
imbalanced signals. CIPS can rank cases for investigation, but its output remains a
decision-support priority rather than proof of fraud or default.

### Use case C: Sales, price, or revenue prediction

Example target: numeric sales or revenue. AWOF configures regression, safely encodes
mixed input data, compares linear and non-linear regressors, selects by RMSE, displays
regression metrics, and provides feature importance. It never describes a regression
prediction as a probability.

### Use case D: Customer segmentation

With no supervised target, the user selects segmentation. AWOF evaluates clustering
capabilities, recommends compatible clustering algorithms, and reports valid cluster
quality metrics. Explainability uses cluster profiles/differences. CIPS is not generated
because segmentation alone does not define business risk.

### Use case E: Academic/research workflow comparison

The project can demonstrate how an adaptive pipeline differs from a reasonable fixed
baseline. It records module/model reductions and measured runtime, memory, and model
quality without exaggerating generality or statistical significance.

## 6. Frontend pages and routes

| Route | Purpose |
| --- | --- |
| `/` | Persisted project overview and recent projects |
| `/upload` | CSV/Excel upload and preview |
| `/datasets/{id}/intelligence` | Profile, quality, EDA, and visual insights |
| `/datasets/{id}/configure` | Objective and target selection |
| `/datasets/{id}/capabilities` | ACSA decisions and evidence |
| `/datasets/{id}/workflow` | AWGA graph, pruning, and node details |
| `/datasets/{id}/execution` | Execution audit timeline |
| `/datasets/{id}/models` | AMRA and training progress |
| `/datasets/{id}/evaluation` | Metrics, best model, and Matplotlib charts |
| `/datasets/{id}/explainability` | Global and local explanations |
| `/datasets/{id}/business` | CIPS dashboard and ranked table |
| `/datasets/{id}/research` | Fixed pipeline versus AWOF comparison |
| `/datasets/{id}/report` | Print/PDF final report |

The interface is implemented with React, TypeScript, Vite, React Router, and React
Flow. It includes responsive navigation, cards, charts, tables, empty states, error
handling, and reusable stage components.

## 7. Backend API groups

All primary APIs are under `/api/v1`.

| API group | Important operations |
| --- | --- |
| Health | application and database health |
| Datasets | upload, list, metadata, preview, summary, history, report, delete |
| Profiling | generate/retrieve profile and visual insights |
| Configuration | objectives, target candidates, save/retrieve configuration |
| Capabilities | generate/retrieve ACSA result |
| Workflow | generate/retrieve AWGA workflow |
| Execution | prune/retrieve pruned workflow, execute/retrieve audit |
| Models | recommend, train, poll training job, retrieve evaluation |
| Explainability | generate/retrieve global and local explanations |
| Business | generate/retrieve CIPS priorities |
| Experiments | run, list, and retrieve research comparisons |

Interactive OpenAPI documentation is available from `/docs` when the backend runs.

## 8. Technical architecture

```text
Browser
  |
React + TypeScript + Vite
  |
REST /api/v1
  |
FastAPI services
  |-- Pandas / NumPy / SciPy profiling and processing
  |-- Scikit-learn model pipelines
  |-- Matplotlib evaluation artifacts
  |-- Joblib fitted pipeline artifacts
  |
SQLAlchemy persistence
  |-- SQLite for local development/tests
  `-- PostgreSQL for production
```

### Main technologies

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, React Router, React Flow |
| Backend/API | Python, FastAPI, Uvicorn, Pydantic |
| Data analysis | Pandas, NumPy, SciPy |
| Machine learning | Scikit-learn, optional XGBoost |
| Visual artifacts | Matplotlib |
| Persistence | SQLAlchemy, Alembic, SQLite/PostgreSQL |
| File formats | CSV, OpenPyXL for XLSX, xlrd for XLS |
| Deployment | Docker, Docker Compose, Nginx, PostgreSQL |
| Tests | Pytest, FastAPI/httpx integration testing |

## 9. Important project folders

| Folder | Responsibility |
| --- | --- |
| `awof/profiler/` | type detection, statistics, quality, outliers, distributions |
| `awof/configuration/` | objectives and target analysis |
| `awof/acsa/` | capability registry, rules, thresholds, scoring |
| `awof/awga/` | nodes, dependencies, DAG generation and validation |
| `awof/pruning/` | live pruning rules and optimized graph generation |
| `awof/execution/` | execution context, module registry, timeline executor |
| `awof/preprocessing/` | missing values, duplicates, encoding, scaling, outliers |
| `awof/feature_engineering/` | extraction, selection, feature construction, PCA |
| `awof/amra/` | model registry, suitability, recommendations |
| `awof/ml/` | training, evaluation, validation, model implementations |
| `awof/explainability/` | importance, SHAP integration/fallback logic |
| `awof/cips/` | signal weights, score calculation, prioritization |
| `backend/app/api/` | FastAPI routes |
| `backend/app/services/` | application orchestration and persistence services |
| `backend/app/database/` | database connection, models, and repository |
| `frontend/src/pages/` | complete stage pages |
| `frontend/src/components/` | reusable UI and charts |
| `tests/` | unit, correctness, persistence, and end-to-end regression tests |
| `docs/` | algorithm, architecture, and research documentation |
| `storage/` | uploaded files, model artifacts, and generated charts |
| `experiments/results/` | benchmark metrics, reports, and research charts |

## 10. Persistence and artifacts

The database stores project metadata and compact JSON outputs for completed stages.
Large or binary artifacts stay on disk and are referenced using safe relative paths.

| Location | Data |
| --- | --- |
| Database | dataset metadata, configuration, stage status/history and result JSON |
| `storage/uploads/` | uploaded CSV/Excel source files |
| `storage/models/` | selected fitted scikit-learn pipelines |
| `storage/charts/` | generated evaluation PNG charts |
| `experiments/results/` | research JSON, CSV, Markdown, and charts |

Persisted profiles include a profile-version marker. When profiling behavior changes,
stale incompatible cached profiles are regenerated instead of returning old results.

## 11. Local development setup

From the repository root in PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm.cmd install
cd ..
```

Start the backend:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm.cmd run dev
```

Default URLs:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`
- Swagger API: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/v1/health`

If those ports are already occupied, use explicit alternatives. Example:

```powershell
# Terminal 1
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001

# Terminal 2
cd frontend
$env:VITE_BACKEND_URL="http://127.0.0.1:8001"
npm.cmd run dev -- --host 127.0.0.1 --port 5188 --strictPort
```

The currently verified alternative used during development is frontend port `5188`
with backend port `8001`.

## 12. Verification commands

Run the complete backend regression suite from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest
```

Compile all Python modules:

```powershell
.\backend\.venv\Scripts\python.exe -m compileall awof backend experiments
```

Build the production frontend:

```powershell
cd frontend
npm.cmd run build
```

The test suite covers upload formats, profiling correctness, configuration, ACSA,
AWGA, pruning, execution, AMRA, model training/evaluation, explainability, CIPS,
persistence, research experiments, data correctness, and end-to-end audit behavior.

## 13. Docker production-style setup

Copy the environment template and replace placeholder credentials:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

Docker Compose runs:

- PostgreSQL with a durable database volume;
- FastAPI with upload/model/experiment volumes;
- Nginx serving the frontend and proxying `/api/v1`;
- dependency-aware health checks and Alembic migrations.

Stop while retaining volumes:

```powershell
docker compose down
```

## 14. Reliability and safety decisions

- Dataset IDs are UUIDs and are validated.
- Upload names are sanitized and path traversal is blocked.
- External errors do not expose server tracebacks or absolute filesystem paths.
- Database transactions roll back on failure.
- Original source data is kept separate from the execution working copy.
- Identifier and constant columns are excluded from predictive features.
- Learned preprocessing is fitted only on training folds.
- A failed candidate model does not prevent other recommended models from completing.
- Optional/unavailable methods are labelled honestly.
- Profile versioning prevents stale cached intelligence from silently surviving logic
  changes.
- Empty or not-yet-run stages have explicit UI states.

## 15. Current limitations

- Long model training and research experiments run in the backend process; there is no
  Redis/Celery distributed task queue.
- The training-job API improves UI progress reporting but is not a durable external job
  system across process failures.
- Type, target, and business-signal detection are heuristic and require human review.
- SHAP is optional; clearly labelled native, linear, or permutation fallbacks may be
  used instead.
- Native tree importance describes model reliance, not causal impact or signed local
  contribution.
- CIPS is decision support, not proof that intervention will change an outcome.
- Research results apply to the selected dataset and environment and do not prove
  universal performance superiority.
- Local artifact storage is suitable for a single-host installation. Multi-host
  deployment needs shared object storage, backups, monitoring, and task workers.

## 16. Short summary

AWOF is an explainable adaptive analytics framework, not just a model-training page.
It implements the full path from real CSV/Excel ingestion through profiling,
configuration, capability scoring, dynamic workflow generation, pruning, execution,
model recommendation, leakage-safe evaluation, explainability, business prioritization,
research comparison, persistence, dashboards, and a printable final report.

Its main value is transparency: every major stage exposes the data signals, decision,
status, measured output, and limitations that produced the next result.
