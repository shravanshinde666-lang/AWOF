from datetime import datetime,timezone
from uuid import uuid4
from .dependencies import MAP,ORDER
from .graph import WorkflowGraph
from .node import WorkflowNode
from .validator import validate_graph
class AWGAGenerator:
 def __init__(self,profile,configuration,acsa):self.profile,self.configuration,self.acsa=profile,configuration,acsa
 def generate(self):
  caps={x["id"]:x for x in self.acsa["capabilities"]};task=self.configuration["problem_type"];included={k for k,v in caps.items() if v["decision"]=="run" and (k not in {"classification","regression","clustering"} or k==task)}
  if task in {"classification","regression","clustering"}:included.add(task)
  optional=[];excluded=[]
  for k,v in caps.items():
   if v["decision"]=="optional":
    s=v["signals"]; ok=(k=="scaling" and task=="clustering") or (k=="encoding" and task in {"classification","regression","clustering"} and s.get("categorical_feature_columns",0)>0) or (k=="feature_selection" and (s.get("feature_columns",0)>=20 or s.get("identifier_candidates",0)>0 or s.get("constant_columns",0)>0)) or (k=="explainability" and task in {"classification","regression"}) or (k=="dimensionality_reduction" and (task=="clustering" or s.get("numeric_feature_columns",0)>=20))
    if ok:included.add(k);optional.append({"capability_id":k,"reason":"Included by deterministic task/dependency resolution."})
    else:excluded.append({"capability_id":k,"decision":"optional","score":v["score"],"reason":"Optional capability was not required."})
   elif k not in included:excluded.append({"capability_id":k,"decision":v["decision"],"score":v["score"],"reason":v["reasons"][0]})
  g=WorkflowGraph();g.add_node(WorkflowNode("dataset_input","Dataset Input","input",None,"core",True,reason="Core workflow node"));g.add_node(WorkflowNode("profile","Dataset Profile","profiling",None,"core",True,["dataset_input"],"Core workflow node"));g.add_edge("dataset_input","profile");prior="profile"
  for nid in ORDER:
   found=next(((k,m) for k,m in MAP.items() if m[0]==nid and k in included),None)
   if not found:continue
   k,(node,label,cat)=found;v=caps[k];reason=next((x["reason"] for x in optional if x["capability_id"]==k),f"ACSA score {v['score']:.2f} → {v['decision'].upper()}")
   g.add_node(WorkflowNode(node,label,cat,k,"selected" if v["decision"]=="run" else "optional",v["decision"]=="run",[prior],reason,{"acsa_score":v["score"],"source_decision":v["decision"]}));g.add_edge(prior,node);prior=node
  g.add_node(WorkflowNode("output","Workflow Output","output",None,"core",True,[prior],"Core workflow node"));g.add_edge(prior,"output");val=validate_graph(g,task);order=g.topological_sort()
  return {"workflow_id":str(uuid4()),"dataset_id":self.configuration["dataset_id"],"algorithm":"AWGA","algorithm_version":"AWGA-1.0","problem_type":task,"business_objective":self.configuration["business_objective"]["id"],"generated_at":datetime.now(timezone.utc).isoformat(),"nodes":[g.nodes[x].to_dict() for x in order],"edges":g.edges,"execution_order":order,"summary":{"total_nodes":len(order),"adaptive_nodes":len(order)-3,"core_nodes":3,"included_run_capabilities":sum(caps[x]["decision"]=="run" for x in included),"included_optional_capabilities":len(optional),"excluded_capabilities":len(excluded)},"validation":val,"excluded_capabilities":excluded,"optional_included":optional}
