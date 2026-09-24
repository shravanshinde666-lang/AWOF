#!/bin/sh
set -eu

attempt=0
until python - <<'PY'
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
with engine.connect() as connection:
    connection.execute(text("SELECT 1"))
PY
do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "Database did not become available before startup timeout" >&2
    exit 1
  fi
  sleep 2
done

alembic -c /app/alembic.ini upgrade head
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
