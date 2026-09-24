from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...schemas.workflow import WorkflowResult
from ...services.workflow_service import generate_workflow,get_workflow,WorkflowNotFoundError
from ...services.configuration_service import ConfigurationNotFoundError
from ...services.capability_service import CapabilityResultNotFoundError
from ...services.dataset_service import DatasetNotFoundError
router=APIRouter(prefix="/datasets",tags=["AWGA Adaptive Workflows"])
def error(code,msg):return JSONResponse(status_code=code,content={"success":False,"error":msg})
@router.post("/{dataset_id}/workflow",response_model=WorkflowResult)
async def generate(dataset_id:str):
 try:return WorkflowResult.model_validate(generate_workflow(dataset_id))
 except CapabilityResultNotFoundError:return error(400,"Capability analysis must be completed before workflow generation.")
 except ConfigurationNotFoundError:return error(400,"A valid analysis configuration is required.")
 except DatasetNotFoundError as exc:return error(404,str(exc))
@router.get("/{dataset_id}/workflow",response_model=WorkflowResult)
async def retrieve(dataset_id:str):
 try:return WorkflowResult.model_validate(get_workflow(dataset_id))
 except WorkflowNotFoundError as exc:return error(404,str(exc))
