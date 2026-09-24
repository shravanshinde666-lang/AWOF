from dataclasses import asdict, dataclass, field
from typing import Any
@dataclass
class WorkflowNode:
 id:str; label:str; category:str; capability_id:str|None; status:str; required:bool; dependencies:list[str]=field(default_factory=list); reason:str=""; metadata:dict[str,Any]=field(default_factory=dict)
 def to_dict(self): return asdict(self)
