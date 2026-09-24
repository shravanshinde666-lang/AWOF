# AWOF

Adaptive Workflow Optimization Framework

## Current Development Stage

Phase 10 - Final Production Readiness + End-to-End Audit

## Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Python
- Data Science: Pandas + NumPy + SciPy + Scikit-learn

## Development Setup

Backend setup commands:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Frontend setup commands:

```powershell
cd frontend
npm.cmd install
```

## Running the Project

From the repository root, start the backend:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

From the `frontend` folder, start the frontend:

```powershell
npm.cmd run dev
```

## URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Dataset Upload & Preview

- Supported formats: CSV, XLSX, XLS
- Maximum upload size: 50 MB
- Upload endpoint: POST /api/v1/datasets/upload
- Frontend route: http://localhost:5173/upload
- Storage: storage/uploads/ (ignored by Git)

## Dataset Intelligence Engine

AWOF can generate a dataset profile after an upload. The profile is computed from
the uploaded tabular data and includes:

- automatic broad type detection and cardinality information
- descriptive statistics for numerical and categorical attributes
- missing-value and duplicate-row analysis
- IQR-based outlier detection
- numerical distribution histogram data
- Pearson correlation pairs for suitable numerical attributes

The profiling API uses an explicit generate-and-retrieve flow:

- `POST /api/v1/datasets/{dataset_id}/profile` generates and stores a durable profile
- `GET /api/v1/datasets/{dataset_id}/profile` retrieves a previously generated profile

The Dataset Intelligence page is available at:
`http://localhost:5173/datasets/{dataset_id}/intelligence`.

Dataset intelligence is detection and description only. It does not clean data,
impute missing values, remove duplicates or outliers, encode features, or train
models. See [Dataset Intelligence algorithm documentation](docs/algorithms/dataset_intelligence.md)
for methods and limitations.

## Analysis Configuration

After profiling a dataset, configure the business objective and, where required,
select a user-approved target column:

Upload → Profile → Configure Objective → Select Target → Ready for ACSA

Objectives and target candidates are served by the backend. Target suggestions are
heuristic assistance only; AWOF does not claim perfect semantic understanding and
the user makes the final selection. Configuration is persisted with the project.

## ACSA Capability Decisions

After configuration, ACSA combines the dataset profile and user-approved
configuration into deterministic capability scores. Each score produces a Run,
Optional, or Skip decision with stored signals and reasons:

Upload → Profile → Configure → ACSA → Capability Decisions

ACSA only recommends capabilities. It does not clean data, transform features,
or train models.

## Adaptive Workflow Generation

AWGA converts the validated configuration and ACSA decisions into a stored,
validated directed acyclic graph. The workflow is generated only; it does not
execute preprocessing or machine learning.

Upload → Profile → Configure → ACSA → AWGA → Dynamic DAG

## Pruning and Execution

AWOF now prunes generated workflows against the live dataset, then executes
supported preprocessing on a working copy only. Current execution supports
duplicates, missing values, IQR reporting, encoding, scaling, filtering, PCA,
and basic temporal preparation. Leakage-safe model evaluation follows as a
separate Phase 6 pipeline.

## AMRA and Machine Learning

The current adaptive flow is:

Upload → Profile → Configure → ACSA → AWGA → Prune → Execute → AMRA → Train Recommended Models → Evaluate → Explain → Business Priority

AMRA uses stored profile, configuration, execution, and dataset signals to rank
models deterministically before training. It recommends up to three supervised
models or two clustering models; optional XGBoost is reported as unavailable
when it is not installed. Training evaluates only those recommendations and
serializes the selected best fitted pipeline under `storage/models/`.

Final supervised evaluation deliberately does not reuse Phase 5's demonstration
preprocessing. It splits raw selected features first and fits imputation,
encoding, and model-specific scaling inside a training-only scikit-learn
pipeline to prevent leakage. See [AMRA](docs/algorithms/amra.md) and the
[ML engine architecture](docs/architecture/ml_engine.md).

## Explainability and Business Priority

AWOF explains the stored best fitted pipeline without retraining it. Global
importance preserves transformed feature names and local requests are bounded.
SHAP is optional; this installation transparently uses model-native and linear
fallback methods because SHAP is unavailable.

CIPS combines a supervised prediction signal with only the business variables
that can be conservatively detected, normalizes available weights dynamically,
and ranks at most 100 entities by default. Clustering workflows correctly report
business prioritization as not applicable. See [Explainability](docs/algorithms/explainability.md)
and [CIPS](docs/algorithms/cips.md).

## Research Experiment & Benchmarking

Phase 8 compares a deterministic, reasonable fixed tabular pipeline with the
actual adaptive AWOF pipeline. It measures named workflow modules, models
trained, elapsed time, measured process memory, and problem-appropriate model
performance over configurable repeated runs.

```text
Dataset -> Fixed Baseline -> Benchmark -> Compare -> Research Evidence
Dataset -> AWOF Pipeline -> Benchmark -> Compare -> Research Evidence
```

The comparison uses the same supervised split policy, target, source rows, and
random state on both paths. It produces factual observations rather than claims
of statistical significance. JSON metrics, a CSV summary, Markdown report, and
simple charts are written beneath `experiments/results/`. See the
[experiment design](docs/research/experiment_design.md) and
[benchmark metrics](docs/research/benchmark_metrics.md).

## Database Persistence

AWOF now persists dataset metadata and completed pipeline-stage JSON results.
PostgreSQL is the production database, configured only through `DATABASE_URL`;
SQLite is the lightweight local/test fallback. Uploaded datasets and fitted
models remain safe relative filesystem artifacts while their metadata is stored
durably. See the [database persistence architecture](docs/architecture/database_persistence.md).

For PostgreSQL, copy `.env.example` to `.env`, set `DATABASE_URL`, then run:

```powershell
.\backend\.venv\Scripts\alembic.exe upgrade head
```

## Production Docker Compose

Docker Compose runs the React application behind Nginx, FastAPI, and PostgreSQL
as separate services. Copy `.env.example` to `.env` and replace the example
PostgreSQL password before deployment; do not commit `.env`.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

The backend waits for PostgreSQL, applies `alembic upgrade head`, and then starts
only after the dependency is reachable. The frontend proxies `/api/` requests to
the backend. Health endpoints are available at `/api/v1/health` through the
frontend or directly at `http://localhost:8000/api/v1/health`. To stop the local
stack while retaining named volumes, run `docker compose down`.

See the [final production architecture](docs/architecture/final_production_overview.md)
and the [algorithm overview](docs/algorithms/overview.md) for components,
data flow, methods, and limitations.

## Known Limitations

- Uploads, trained models, and research artifacts use local mounted volumes; a
  multi-host deployment needs shared durable object storage.
- Long-running training and benchmarking execute in the request process. There
  is no background job queue in this release.
- ACSA, AWGA, AMRA, and CIPS are deterministic decision-support methods, not
  guarantees of business outcomes. CIPS is deliberately unavailable where its
  business-risk interpretation is not supported by the workflow.
- SHAP is used only when compatible and installed; transparent native, linear,
  or permutation fallbacks are otherwise reported by the API.
