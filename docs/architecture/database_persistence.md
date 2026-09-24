# Database persistence architecture

Phase 9 makes PostgreSQL the production source of truth for AWOF state.
SQLite is a lightweight local-development and test fallback only.

## Stored records

`datasets` stores safe upload metadata and the relative stored filename. The
uploaded source data and fitted `.joblib` model remain filesystem artifacts.
`dataset_stages` stores JSON results for profile, configuration, ACSA, AWGA,
pruning, execution, AMRA, evaluation, explainability, and CIPS. The JSON shape
matches the existing API contracts, so algorithm outputs are not unnecessarily
decomposed into brittle relational tables.

`research_experiments` stores durable experiment history and its compact JSON
result. Per-experiment charts, reports, and metric files remain under
`experiments/results/`.

## Transactions and safety

Every repository operation runs inside a SQLAlchemy session scope. Exceptions
roll back the transaction and are logged server-side; API responses expose only
safe error messages. Dataset and experiment identifiers are parsed as UUIDs.
Stored filenames are sanitized and checked as relative basenames before any
filesystem access.

Deleting a dataset removes its database stages and experiments first, then its
safe upload and dataset-prefixed model artifacts. It never accepts an arbitrary
filesystem path.

## Setup

For production, set `DATABASE_URL` in `.env`:

```text
DATABASE_URL=postgresql+psycopg://awof_user:password@localhost:5432/awof
```

Run migrations from the repository root:

```powershell
.\backend\.venv\Scripts\alembic.exe upgrade head
```

For a new migration after changing ORM models:

```powershell
.\backend\.venv\Scripts\alembic.exe revision --autogenerate -m "describe change"
```

The default local URL is a SQLite file at `storage/awof.db`; its schema is
created automatically for local/test use. PostgreSQL deployments should use
Alembic migrations rather than automatic schema creation.
