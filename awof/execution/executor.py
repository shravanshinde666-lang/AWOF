import time
from .context import ExecutionContext
from .module_registry import REGISTRY
def execute(pruned,df,dataset_id,target,problem,business):
 ctx=ExecutionContext(dataset_id,pruned["pruned_workflow_id"],df.copy(deep=True),df.copy(deep=True),target,[c for c in df.columns if c!=target],problem,business);results=[];start=time.perf_counter()
 for node in pruned["nodes"]:
  before=ctx.working_dataframe.shape;t=time.perf_counter();status="completed";details={}
  if node["id"] in REGISTRY:
   try:details=REGISTRY[node["id"]](ctx.working_dataframe,ctx)
   except Exception as exc:status="failed";ctx.errors.append(str(exc))
  elif node["id"] in {"classification","regression","clustering","explainability","business_prioritization"}:status="skipped";details={"reason":"Execution implemented in later phase."}
  results.append({"node_id":node["id"],"status":status,"duration_ms":round((time.perf_counter()-t)*1000,3),"rows_before":before[0],"rows_after":ctx.working_dataframe.shape[0],"columns_before":before[1],"columns_after":ctx.working_dataframe.shape[1],"details":details})
  if status=="failed":break
 return {"dataset_id":dataset_id,"workflow_id":pruned["pruned_workflow_id"],"node_results":results,"summary":{"total_nodes":len(pruned["nodes"]),"executed_nodes":sum(x["status"]=="completed" for x in results),"pruned_nodes":len(pruned["pruned_nodes"]),"skipped_nodes":sum(x["status"]=="skipped" for x in results),"failed_nodes":sum(x["status"]=="failed" for x in results),"total_duration_ms":round((time.perf_counter()-start)*1000,3),"initial_rows":df.shape[0],"final_rows":ctx.working_dataframe.shape[0],"initial_columns":df.shape[1],"final_columns":ctx.working_dataframe.shape[1]},"warnings":ctx.warnings,"errors":ctx.errors}
