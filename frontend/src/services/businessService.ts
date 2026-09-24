import api from "./api";
import type { BusinessPriorityResult } from "../types/business";

const base = (datasetId: string) => `/datasets/${encodeURIComponent(datasetId)}/business-priority`;

export const generateBusinessPriority = (datasetId: string) => api.post<BusinessPriorityResult>(base(datasetId)).then((response) => response.data);
export const getBusinessPriority = (datasetId: string) => api.get<BusinessPriorityResult>(base(datasetId)).then((response) => response.data);
