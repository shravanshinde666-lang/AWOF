import api from "./api";
import type {
  ExplainabilityResult,
  InferenceSchemaResponse,
  LocalExplanation,
  PredictionResponse,
} from "../types/explainability";

const base = (datasetId: string) => `/datasets/${encodeURIComponent(datasetId)}`;

export const generateExplainability = (datasetId: string) =>
  api.post<ExplainabilityResult>(`${base(datasetId)}/explain`).then((response) => response.data);

export const getExplainability = (datasetId: string) =>
  api.get<ExplainabilityResult>(`${base(datasetId)}/explainability`).then((response) => response.data);

export const getLocalExplanation = (datasetId: string, rowIndex: number) =>
  api.get<LocalExplanation>(`${base(datasetId)}/explainability/${rowIndex}`).then((response) => response.data);

export const getInferenceSchema = (datasetId: string) =>
  api.get<InferenceSchemaResponse>(`${base(datasetId)}/inference/schema`).then((response) => response.data);

export const predictLive = (
  datasetId: string,
  features: Record<string, string | number | null>,
  targetClass?: string | null,
) =>
  api
    .post<PredictionResponse>(`${base(datasetId)}/inference/predict`, {
      features,
      target_class: targetClass ?? null,
    })
    .then((response) => response.data);
