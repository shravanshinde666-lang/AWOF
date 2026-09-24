from typing import Any
from pydantic import BaseModel
class WorkflowNodeSchema(BaseModel): id:str;label:str;category:str;capability_id:str|None;status:str;required:bool;dependencies:list[str];reason:str;metadata:dict[str,Any]
class WorkflowEdgeSchema(BaseModel): source:str;target:str
class WorkflowResult(BaseModel):
 workflow_id:str;dataset_id:str;algorithm:str;algorithm_version:str;problem_type:str;business_objective:str;generated_at:str;nodes:list[WorkflowNodeSchema];edges:list[WorkflowEdgeSchema];execution_order:list[str];summary:dict[str,int];validation:dict[str,Any];excluded_capabilities:list[dict[str,Any]];optional_included:list[dict[str,str]]
