import api from "./api";
import type { ExplainabilityResult, LocalExplanation } from "../types/explainability";

const base = (datasetId: string) => `/datasets/${encodeURIComponent(datasetId)}`;

export const generateExplainability = (datasetId: string) => api.post<ExplainabilityResult>(`${base(datasetId)}/explain`).then((response) => response.data);
export const getExplainability = (datasetId: string) => api.get<ExplainabilityResult>(`${base(datasetId)}/explainability`).then((response) => response.data);
export const getLocalExplanation = (datasetId: string, rowIndex: number) => api.get<LocalExplanation>(`${base(datasetId)}/explainability/${rowIndex}`).then((response) => response.data);
