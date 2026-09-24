from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...schemas.capability import ACSAResult
from ...services.capability_service import CapabilityResultNotFoundError, generate_capabilities, get_capabilities
from ...services.configuration_service import ConfigurationNotFoundError
from ...services.dataset_service import DatasetNotFoundError

router = APIRouter(prefix="/datasets", tags=["ACSA Capability Scoring"])

def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": False, "error": message})

@router.post("/{dataset_id}/capabilities", response_model=ACSAResult)
async def generate(dataset_id: str) -> ACSAResult | JSONResponse:
    try:
        return ACSAResult.model_validate(generate_capabilities(dataset_id))
    except ConfigurationNotFoundError:
        return error_response(400, "Analysis configuration must be completed before capability scoring.")
    except DatasetNotFoundError as error:
        return error_response(404, str(error))

@router.get("/{dataset_id}/capabilities", response_model=ACSAResult)
async def retrieve(dataset_id: str) -> ACSAResult | JSONResponse:
    try:
        return ACSAResult.model_validate(get_capabilities(dataset_id))
    except CapabilityResultNotFoundError as error:
        return error_response(404, str(error))
