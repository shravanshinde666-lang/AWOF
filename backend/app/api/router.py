from fastapi import APIRouter

from .routes import business, capabilities, configuration, datasets, execution, experiments, explainability, health, models, profiling, workflows


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(datasets.router)
api_router.include_router(profiling.router)
api_router.include_router(configuration.router)
api_router.include_router(capabilities.router)
api_router.include_router(workflows.router)
api_router.include_router(execution.router)
api_router.include_router(models.router)
api_router.include_router(explainability.router)
api_router.include_router(business.router)
api_router.include_router(experiments.router)
