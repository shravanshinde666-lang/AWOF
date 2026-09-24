import api from "./api";
import type { AMRAResult, ModelEvaluationResult } from "../types/model";

const base = (datasetId: string) => `/datasets/${encodeURIComponent(datasetId)}/models`;

export const recommendModels = (datasetId: string) => api.post<AMRAResult>(`${base(datasetId)}/recommend`).then((response) => response.data);
export const getRecommendations = (datasetId: string) => api.get<AMRAResult>(`${base(datasetId)}/recommendations`).then((response) => response.data);
export const trainModels = (datasetId: string) => api.post<ModelEvaluationResult>(`${base(datasetId)}/train`).then((response) => response.data);
export const getEvaluation = (datasetId: string) => api.get<ModelEvaluationResult>(`${base(datasetId)}/evaluation`).then((response) => response.data);
