import api from "./api";
const base=(id:string)=>`/datasets/${encodeURIComponent(id)}`;
export const pruneWorkflow=(id:string)=>api.post(base(id)+"/workflow/prune").then(r=>r.data);
export const getPrunedWorkflow=(id:string)=>api.get(base(id)+"/workflow/pruned").then(r=>r.data);
export const executeWorkflow=(id:string)=>api.post(base(id)+"/execute").then(r=>r.data);
export const getExecution=(id:string)=>api.get(base(id)+"/execution").then(r=>r.data);
