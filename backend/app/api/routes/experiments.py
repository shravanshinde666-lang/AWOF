from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.experiment import ExperimentRequest, ExperimentSummary, ResearchExperimentResult
from ...services.experiment_service import (
    ExperimentNotFoundError,
    ExperimentPrerequisiteError,
    get_dataset_experiments,
    get_experiment,
    run_comparison,
)


router = APIRouter(tags=["Research Experiments"])


def _response(action):
    try:
        return action()
    except ExperimentPrerequisiteError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except ExperimentNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})


@router.post("/datasets/{dataset_id}/experiments/compare", response_model=ResearchExperimentResult)
async def compare(dataset_id: str, request: ExperimentRequest):
    return _response(lambda: run_comparison(dataset_id, request.runs, request.experiment_name))


@router.get("/experiments/{experiment_id}", response_model=ResearchExperimentResult)
async def retrieve(experiment_id: str):
    return _response(lambda: get_experiment(experiment_id))


@router.get("/datasets/{dataset_id}/experiments", response_model=list[ExperimentSummary])
async def history(dataset_id: str):
    return _response(lambda: get_dataset_experiments(dataset_id))


@router.get("/datasets/{dataset_id}/experiments/latest", response_model=ResearchExperimentResult)
async def latest(dataset_id: str):
    def action():
        values = get_dataset_experiments(dataset_id)
        if not values:
            raise ExperimentNotFoundError("No experiment has been run for this dataset.")
        return get_experiment(values[0]["experiment_id"])
    return _response(action)
