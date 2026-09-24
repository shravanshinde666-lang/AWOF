# AWOF — Complete Project Documentation

## 1. Project purpose

**AWOF** stands for **Adaptive Workflow Optimization Framework**. It is a
dataset-aware data-science application that helps a user move from an uploaded
tabular dataset to an evaluated and explained machine-learning result.

Unlike a fixed ML notebook, AWOF first studies the dataset and business goal,
then generates and prunes a suitable workflow. Every major result is saved so a
project can be retrieved after a backend restart.

## 2. Complete workflow

```text
Upload dataset
  -> Dataset profile / intelligence
  -> Business objective and target configuration
  -> ACSA capability scoring
  -> AWGA workflow generation
  -> Workflow pruning
  -> Workflow execution / preparation
  -> AMRA model recommendation
  -> Model training and evaluation
  -> Explainability
  -> CIPS business priority ranking
  -> Research benchmark comparison
  -> Persisted project history
```

## 3. What each part does

| Module | Full name | What it does | Why it is useful |
| --- | --- | --- | --- |
| Upload | Dataset ingestion | Accepts CSV, XLSX, and XLS files; validates extension, size, and filename | Starts a safe project from real data |
| Dataset Intelligence | Profiling and EDA | Detects column types, missing values, duplicate rows, IQR outliers, distributions, correlations, and possible ID columns | Explains the data before decisions are made |
| Configuration | Objective and target selection | Lets the user choose a business objective and target column | Prevents the system from guessing an important business decision |
| ACSA | Adaptive Capability Scoring Algorithm | Scores capabilities as **Run**, **Optional**, or **Skip** with reasons | Selects only suitable analysis capabilities |
| AWGA | Adaptive Workflow Generation Algorithm | Produces a validated directed acyclic workflow graph | Shows the exact adaptive plan before execution |
| Pruning | Workflow pruning | Removes nodes that are not applicable and records pruning evidence | Avoids unnecessary processing and keeps decisions transparent |
| Execution | Data preparation engine | Performs supported duplicate handling, missing-value preparation, encoding, scaling, filtering, PCA, temporal preparation, and feature selection | Prepares a working copy for downstream analytics |
| AMRA | Adaptive Model Recommendation Algorithm | Ranks appropriate models for classification, regression, or clustering | Narrows training to models that fit the dataset and objective |
| Training | Leakage-safe ML pipelines | Splits data before fitting preprocessing and model steps; saves the best fitted pipeline | Reduces data leakage and preserves a reusable artifact |
| Evaluation | Model evaluation | Returns model metrics and identifies the selected best model | Lets users compare observed model quality |
| Explainability | SHAP/fallback explanation engine | Produces global feature importance and bounded local row explanations | Answers why the model made a prediction |
| CIPS | Customer Intervention Priority Score | Combines applicable prediction risk and detected business signals into a 0–100 priority score | Helps rank cases for business action instead of merely predicting outcomes |
| Research | Fixed-vs-adaptive benchmark | Compares AWOF against a deterministic baseline and writes metrics, reports, and charts | Creates measurable evidence about workflow behavior |

## 4. Supported analytics types

### Classification

Used when the target is a category, such as `churn`, `fraud`, `yes/no`, or a
customer segment label. AWOF can return class predictions, probabilities where
supported, model metrics, explanations, and business-priority rankings where
the workflow is applicable.

### Regression

Used when the target is numeric, such as `revenue`, `sales`, `price`, or
`amount`. AWOF returns predicted values and regression evaluation metrics.

Regression output is never presented as a probability.

### Clustering

Used when there is no supervised target and the objective is customer/entity
segmentation. AWOF interprets clusters through profiles and distinguishing
features. CIPS correctly returns **not applicable** rather than inventing a
risk score for segmentation-only workflows.

## 5. Models used

The model recommendation and training layers support appropriate available
models from these families:

| Problem type | Model families |
| --- | --- |
| Classification | Logistic Regression, Random Forest Classifier, Gradient Boosting Classifier |
| Regression | Linear Regression, Ridge Regression, Random Forest Regressor, Gradient Boosting Regressor |
| Clustering | Supported clustering models selected by the AMRA workflow |

XGBoost is optional. If it is unavailable in the installed environment, AWOF
reports it as unavailable rather than pretending it was trained.

## 6. Explainability and CIPS

AWOF keeps these three questions separate:

```text
Prediction:      What is likely to happen?
Explainability:  Why did the model produce this output?
CIPS:            Which applicable cases should the business prioritize?
```

Explainability uses SHAP when it is installed and compatible. When it is not,
AWOF transparently uses model-native tree importance, linear coefficients, or
permutation importance and reports the method in the API/UI.

CIPS dynamically detects suitable signals such as risk probability, value,
engagement, support activity, or recency. It uses only signals that are actually
available, redistributes the default weights across them, and calculates:

```text
CIPS = 100 × sum(effective_weight × normalized_signal)
```

Priority levels are:

| Score | Priority |
| --- | --- |
| 85–100 | Immediate |
| 70–<85 | High |
| 40–<70 | Medium |
| 0–<40 | Monitor |

## 7. Technologies used

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Workflow pages, charts, navigation, and user interaction |
| Backend | Python, FastAPI | REST APIs and application services |
| Data processing | Pandas, NumPy | Dataset loading, transformation, profiling, and numerical handling |
| Machine learning | Scikit-learn | Pipelines, preprocessing, models, evaluation, PCA, and feature selection |
| Database | PostgreSQL | Production persistence of project metadata and stage results |
| Local/test DB | SQLite | Lightweight development and test fallback |
| ORM/migrations | SQLAlchemy, Alembic | Database models, transactions, and schema migrations |
| Deployment | Docker, Docker Compose, Nginx | Frontend, backend, and PostgreSQL service deployment |

## 8. Data and result storage

| Location | Stored content |
| --- | --- |
| PostgreSQL / SQLite | Dataset metadata, project history, configurations, workflow results, evaluations, explainability, CIPS, and experiment metadata |
| `storage/uploads/` | Uploaded source datasets |
| `storage/models/` | Saved fitted model pipelines (`.joblib`) |
| `experiments/results/metrics/` | Research experiment JSON/CSV metrics |
| `experiments/results/reports/` | Research Markdown reports |
| `experiments/results/charts/` | Research comparison charts |

The database stores safe relative artifact metadata rather than exposing
absolute filesystem paths.

## 9. Frontend pages

| Route | Page |
| --- | --- |
| `/` | AWOF overview dashboard |
| `/upload` | Dataset upload |
| `/datasets/{id}/intelligence` | Dataset intelligence and EDA |
| `/datasets/{id}/configure` | Business objective and target configuration |
| `/datasets/{id}/capabilities` | ACSA results |
| `/datasets/{id}/workflow` | AWGA workflow and pruning evidence |
| `/datasets/{id}/execution` | Workflow execution results |
| `/datasets/{id}/models` | AMRA model recommendations and training |
| `/datasets/{id}/evaluation` | Model metrics and best model |
| `/datasets/{id}/explainability` | Global/local model explanations |
| `/datasets/{id}/business` | CIPS business-priority ranking |
| `/datasets/{id}/research` | Fixed baseline vs AWOF research comparison |

## 10. Relation to the Data Science syllabus

| Unit | AWOF implementation |
| --- | --- |
| Unit I — Introduction | Modelling, train/test separation, evaluation, and overfitting/leakage prevention |
| Unit II — Data types/statistics | Attribute detection, mean/median/mode, spread, distributions, missing values, IQR outliers |
| Unit III — Cleaning/preparation | Duplicate handling, missing values, transformations, scaling, outlier reporting, PCA, feature selection |
| Unit IV — Python foundations | Pandas DataFrames, NumPy arrays, indexing, subsetting, matrix-style transformations, PCA |
| Unit V — EDA/feature engineering | Data inspection, correlation analysis, encoding, scaling, model evaluation, confusion-matrix-based classification metrics |
| Unit VI — Visualisation/regression | Histograms, charts, workflow graphs, research charts, Linear Regression, and Ridge Regression |

## 11. Safety and reliability

- UUID project identifiers are validated.
- Upload names are sanitized and filesystem paths are protected from traversal.
- Database sessions roll back on failed transactions.
- API errors avoid sending tracebacks or internal filesystem paths to the user.
- Project deletion removes its database records and associated safe dataset/model/experiment artifacts.
- Backend, frontend, and PostgreSQL support health checks in Docker Compose.
- PostgreSQL migrations run through Alembic during container startup.

## 12. How to run locally

Start the backend from the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://localhost:5173`.

## 13. Current limitations

- Long-running training and research benchmarks run inside the backend request;
  no Redis or Celery background queue is implemented.
- PostgreSQL is the production database, while SQLite is intended only for local
  development and tests.
- SHAP availability depends on the installed Python environment; a clearly
  labelled fallback is used where SHAP cannot run.
- CIPS does not invent business signals that do not exist in the dataset.
- The research comparison reports measured observations and does not claim
  statistical significance.
- The Docker setup is a single-host deployment reference; multi-host systems
  would need shared object storage and operational monitoring.

## 14. Detailed technical documents

- [ACSA](algorithms/acsa.md)
- [AWGA](algorithms/awga.md)
- [Workflow Pruning](algorithms/workflow_pruning.md)
- [AMRA](algorithms/amra.md)
- [Explainability](algorithms/explainability.md)
- [CIPS](algorithms/cips.md)
- [Database Persistence](architecture/database_persistence.md)
- [Execution Engine](architecture/execution_engine.md)
- [ML Engine](architecture/ml_engine.md)
- [Research Experiment Design](research/experiment_design.md)
