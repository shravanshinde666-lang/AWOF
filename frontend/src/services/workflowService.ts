import api from "./api";
import type { WorkflowResult } from "../types/workflow";
const path=(id:string)=>`/datasets/${encodeURIComponent(id)}/workflow`;
export const generateWorkflow=async(id:string):Promise<WorkflowResult>=>(await api.post<WorkflowResult>(path(id))).data;
export const getWorkflow=async(id:string):Promise<WorkflowResult>=>(await api.get<WorkflowResult>(path(id))).data;
