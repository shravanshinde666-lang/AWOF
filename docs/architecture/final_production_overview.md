# Final production architecture

AWOF is deployed as three cooperating services: a browser-facing Nginx frontend,
the FastAPI application, and PostgreSQL. Docker Compose supplies the service
network and durable named volumes for uploads, fitted models, research artifacts,
and database data.

```text
Browser
  |  static UI and /api proxy
Nginx frontend
  |  /api/v1
FastAPI backend  <---->  PostgreSQL (durable project state)
  |
  +--> uploads, model artifacts, experiment reports (mounted volumes)
```

## Startup and health

PostgreSQL has a `pg_isready` health check. The backend waits for a successful
database connection, executes `alembic upgrade head`, then starts Uvicorn. The
backend health endpoint checks application database connectivity. Compose waits
for that backend health check before starting the frontend, whose Nginx health
check is also declared.

## Data flow and persistence

The existing pipeline remains:

```text
Upload -> Profile -> Configure -> ACSA -> AWGA -> Prune -> Execute
       -> AMRA -> Train -> Evaluate -> Explain -> CIPS -> Research
```

Dataset metadata, status history, and compact stage outputs are stored in
PostgreSQL JSON records. Uploaded tabular files and fitted model/experiment
artifacts remain in safe relative locations on mounted volumes. The API never
accepts a client-provided filesystem path. Deleting a project removes its
database records and only the associated safe artifacts.

## Configuration and security

Configuration is environment-driven. `.env.example` contains placeholders only;
real credentials belong in a non-committed `.env` or a deployment secret store.
The database URL is never hardcoded. Upload names are sanitized, UUIDs are
validated, database transactions roll back on failure, and external responses
avoid traceback and filesystem-path disclosure.

## Operational limitations

This compose deployment is a single-host reference configuration. It does not
add Redis, Celery, MLflow, cloud object storage, or horizontal task workers.
Consequently long model/benchmark requests run in the API process, and mounted
volumes must be backed up by the operator.
