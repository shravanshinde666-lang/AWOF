from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.configuration import (
    AnalysisConfiguration,
    ConfigurationRequest,
    ConfigurationResponse,
    ObjectivesResponse,
    TargetCandidatesResponse,
)
from ...services.configuration_service import (
    ConfigurationNotFoundError,
    ConfigurationValidationError,
    get_saved_configuration,
    get_target_candidates,
    list_business_objectives,
    save_configuration,
)
from ...services.dataset_service import DatasetNotFoundError


router = APIRouter(tags=["Analysis Configuration"])


def error_response(status_code: int, error: str, details: list[str] | None = None) -> JSONResponse:
    content: dict[str, object] = {"success": False, "error": error}
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)


@router.get("/configuration/objectives", response_model=ObjectivesResponse)
async def list_objectives() -> ObjectivesResponse:
    return ObjectivesResponse(objectives=list_business_objectives())


@router.get("/datasets/{dataset_id}/target-candidates", response_model=TargetCandidatesResponse)
async def target_candidates(dataset_id: str) -> TargetCandidatesResponse | JSONResponse:
    try:
        return TargetCandidatesResponse(
            dataset_id=dataset_id,
            candidates=get_target_candidates(dataset_id),
        )
    except DatasetNotFoundError as error:
        message = str(error)
        if message == "Dataset profile has not been generated":
            message = "Dataset must be profiled before selecting a target."
        return error_response(404, message)


@router.post("/datasets/{dataset_id}/configuration", response_model=ConfigurationResponse)
async def create_configuration(
    dataset_id: str,
    request: ConfigurationRequest,
) -> ConfigurationResponse | JSONResponse:
    try:
        configuration = save_configuration(
            dataset_id, request.business_objective, request.target_column
        )
        return ConfigurationResponse(
            configuration=AnalysisConfiguration.model_validate(configuration)
        )
    except ConfigurationValidationError as error:
        return error_response(400, "Analysis configuration is invalid.", error.configuration["errors"])
    except DatasetNotFoundError as error:
        return error_response(404, str(error))


@router.get("/datasets/{dataset_id}/configuration", response_model=ConfigurationResponse)
async def retrieve_configuration(
    dataset_id: str,
) -> ConfigurationResponse | JSONResponse:
    try:
        return ConfigurationResponse(
            configuration=AnalysisConfiguration.model_validate(
                get_saved_configuration(dataset_id)
            )
        )
    except ConfigurationNotFoundError as error:
        return error_response(404, str(error))
