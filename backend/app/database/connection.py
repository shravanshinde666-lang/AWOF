"""Database engine and transaction helpers.

SQLite is the local/test fallback. Production deployments set ``DATABASE_URL``
to a PostgreSQL SQLAlchemy URL, for example ``postgresql+psycopg://...``.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..config.settings import settings
from .base import Base


logger = logging.getLogger(__name__)
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_configured_url: str | None = None


def configure_database(url: str | None = None) -> None:
    """Replace the engine; primarily used by isolated persistence tests."""
    global _engine, _session_factory, _configured_url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
    _configured_url = url or settings.DATABASE_URL


def get_engine() -> Engine:
    global _engine, _session_factory, _configured_url
    url = _configured_url or settings.DATABASE_URL
    if _engine is None:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, echo=settings.DATABASE_ECHO, pool_pre_ping=True, connect_args=connect_args)
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return _engine


def init_database() -> None:
    """Create the lightweight SQLite schema; PostgreSQL uses Alembic."""
    engine = get_engine()
    if engine.url.get_backend_name() == "sqlite":
        from . import models  # noqa: F401
        Base.metadata.create_all(engine)


def database_healthy() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    init_database()
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Database transaction rolled back")
        raise
    finally:
        session.close()
