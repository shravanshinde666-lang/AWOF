import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .api.routes import health
from .config.settings import settings
from .database import database_healthy, init_database


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize persistence without leaking database details to clients."""
    try:
        init_database()
        if not database_healthy():
            logger.error("Database health check failed during startup")
    except Exception:
        logger.exception("Database initialization failed during startup")
    yield

app = FastAPI(
    title="AWOF — Adaptive Workflow Optimization Framework",
    description="Dataset-aware adaptive analytics and machine learning platform.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception while processing %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
    )
