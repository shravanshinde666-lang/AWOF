from fastapi import APIRouter

from ...database import database_healthy


router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "AWOF",
        "message": "Adaptive Workflow Optimization Framework API",
        "status": "running",
        "version": "0.1.0",
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    database = "healthy" if database_healthy() else "unavailable"
    return {
        "status": "healthy" if database == "healthy" else "degraded",
        "backend": "FastAPI",
        "service": "AWOF",
        "database": database,
    }
