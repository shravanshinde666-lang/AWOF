from copy import deepcopy
from uuid import uuid4

CORE={"dataset_input","profile","output","classification","regression","clustering"}
def prune(workflow,df,target_column,problem_type):
 kept=[];decisions=[];features=[c for c in df.columns if c!=target_column]
 for node in workflow["nodes"]:
  nid=node["id"];reason=None
  if nid not in CORE:
   if nid=="missing_values" and df[features].isna().sum().sum()==0:reason="No feature missing values remain."
   elif nid=="duplicate_handling" and not df.duplicated().any():reason="No duplicate rows remain."
   elif nid=="encoding" and not any(df[c].dtype=="object" or str(df[c].dtype)=="bool" for c in features):reason="No categorical feature columns remain."
   elif nid=="scaling" and (not any(str(df[c].dtype).startswith(("int","float")) for c in features) or problem_type not in {"clustering"} and "dimensionality_reduction" not in [n["id"] for n in workflow["nodes"]]):reason="No usable numerical features or scaling dependency remains."
   elif nid=="dimensionality_reduction" and sum(str(df[c].dtype).startswith(("int","float")) for c in features)<2:reason="PCA requires at least two numerical features."
   elif nid=="feature_selection" and len(features)<5:reason="Small feature set has no immediate filtering benefit."
   elif nid=="outlier_analysis" and not any(str(df[c].dtype).startswith(("int","float")) for c in features):reason="No suitable numerical columns remain."
  decisions.append({"node_id":nid,"original_status":node["status"],"pruning_decision":"prune" if reason else "keep","reason":reason or "Retained for current execution context.","signals":{}})
  if not reason:kept.append(node)
 ids=[n["id"] for n in kept];edges=[{"source":ids[i],"target":ids[i+1]} for i in range(len(ids)-1)]
 return {"original_workflow_id":workflow["workflow_id"],"pruned_workflow_id":str(uuid4()),"algorithm":"Workflow Pruning Engine","algorithm_version":"PRUNE-1.0","nodes":kept,"edges":edges,"execution_order":ids,"pruned_nodes":[d for d in decisions if d["pruning_decision"]=="prune"],"summary":{"total_nodes":len(ids),"pruned_nodes":len(workflow["nodes"])-len(ids)},"validation":{"valid":True,"is_dag":True,"errors":[],"warnings":[]}}
