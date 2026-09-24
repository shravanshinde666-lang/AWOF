from typing import Any
from pydantic import BaseModel
class PruningDecision(BaseModel):node_id:str;original_status:str;pruning_decision:str;reason:str;signals:dict[str,Any]
class NodeExecutionResult(BaseModel):node_id:str;status:str;duration_ms:float;rows_before:int;rows_after:int;columns_before:int;columns_after:int;details:dict[str,Any]
class ExecutionResult(BaseModel):dataset_id:str;workflow_id:str;node_results:list[NodeExecutionResult];summary:dict[str,Any];warnings:list[str];errors:list[str]
