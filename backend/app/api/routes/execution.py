from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...schemas.execution import ExecutionResult
from ...services.execution_service import prune_workflow,get_pruned,execute_workflow,get_execution
router=APIRouter(prefix="/datasets",tags=["Workflow Pruning and Execution"])
def call(fn):
 try:return fn()
 except KeyError as e:return JSONResponse(status_code=404,content={"success":False,"error":str(e)})
@router.post("/{dataset_id}/workflow/prune")
async def prune_route(dataset_id:str):return call(lambda:prune_workflow(dataset_id))
@router.get("/{dataset_id}/workflow/pruned")
async def pruned_route(dataset_id:str):return call(lambda:get_pruned(dataset_id))
@router.post("/{dataset_id}/execute",response_model=ExecutionResult)
async def execute_route(dataset_id:str):return call(lambda:execute_workflow(dataset_id))
@router.get("/{dataset_id}/execution",response_model=ExecutionResult)
async def execution_route(dataset_id:str):return call(lambda:get_execution(dataset_id))
