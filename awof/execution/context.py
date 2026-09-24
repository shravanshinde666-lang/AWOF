from dataclasses import dataclass,field
from typing import Any
@dataclass
class ExecutionContext:
 dataset_id:str;workflow_id:str;original_dataframe:Any;working_dataframe:Any;target_column:str|None;feature_columns:list[str];problem_type:str;business_objective:str;artifacts:dict=field(default_factory=dict);metrics:dict=field(default_factory=dict);execution_log:list=field(default_factory=list);warnings:list=field(default_factory=list);errors:list=field(default_factory=list)
